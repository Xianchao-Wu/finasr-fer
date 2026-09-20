"""Robust LLM-backed financial fact extractor for FER v0.7.1.

Changes vs v0.7:
- disables Qwen3 thinking by default
- deterministic extraction settings
- tighter output contract and max-fact cap
- detects finish_reason='length'
- robustly parses JSON/code fences/leading text
- retries with a shorter repair prompt
- records useful diagnostics without treating extraction failure as []
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

SYSTEM_PROMPT = r"""You are a multilingual financial information extraction engine.
Convert the ASR transcript into atomic structured financial facts for Financial Error Rate (FER) evaluation.
Extraction MUST be reference-independent: use only the supplied transcript and language. Do not repair the transcript
using world knowledge and do not infer values or entities that are not explicitly stated.

Return JSON only with exactly this top-level structure:
{{"facts": [ ... ]}}

Each fact may contain:
- fact_id: H1, H2, ...
- entity: company / bank / institution / financial subject explicitly associated with the fact
- metric: canonical financial metric stated in the transcript
- value: canonical numeric value as a JSON number
- surface_value: exact value phrase from the transcript
- unit: absolute_money, ratio, delta, count, multiple, or another short canonical label
- currency: ISO code such as USD, CNY, JPY, EUR, GBP when explicitly recoverable
- time: canonical fiscal/calendar scope, e.g. FY2027Q2, FY2027, 2026Q3, 2026
- negation: boolean
- comparison: at_least, at_most, greater_than, less_than, or null
- direction: increase, decrease, unchanged, or null
- term: optional canonical financial term for a meaningful non-numeric proposition
- ticker: optional explicitly stated ticker
- acronym: optional explicitly stated financial acronym
- confidence: number in [0,1]

Canonicalization rules:
1. Money -> base currency units: "$12.6 billion" -> value=12600000000, currency="USD", unit="absolute_money".
2. Percentages -> ratios: "12.6%" / "12.6 percent" / "12.6パーセント" -> value=0.126, unit="ratio".
3. Basis points -> ratio deltas: "35 basis points" -> value=0.0035, unit="delta".
4. Chinese/Japanese large-number units: 亿/億=1e8, 万=1e4.
5. Normalize explicit fiscal time only; do not invent missing years.
6. Bind each quantity to the correct local entity and metric.
7. Preserve above/below, increase/decrease, and negation semantics.
8. One fact per atomic proposition; never duplicate a proposition.
9. Do not output years/quarter indices as standalone values when they only express time.
10. If no financial fact is present, return {{"facts": []}}.

STRICT OUTPUT RULES:
- JSON only. No Markdown, explanations, analysis, reasoning, comments, or chain-of-thought.
- Do not repeat the transcript.
- Keep fields concise.
- Return at most {max_facts} facts. Prefer fewer high-confidence explicit facts over speculative facts.
"""

USER_TEMPLATE = "Language: {language}\nTranscript:\n{text}\n\nReturn the JSON object now."


class LLMFinancialFactExtractor:
    def __init__(self, base_url="http://127.0.0.1:8000/v1", model="qwen3-financial-extractor",
                 api_key: Optional[str]=None, temperature: float=0.0, max_tokens: int=1536,
                 timeout: int=180, retries: int=2, max_facts: int=30,
                 disable_thinking: bool=True, debug: bool=False):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "EMPTY")
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.timeout = int(timeout)
        self.retries = int(retries)
        self.max_facts = int(max_facts)
        self.disable_thinking = bool(disable_thinking)
        self.debug = bool(debug)

    @staticmethod
    def _language_name(language: str) -> str:
        return {"en":"English", "zh":"Mandarin Chinese", "ja":"Japanese"}.get(language, language)

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        text = (text or "").strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    @classmethod
    def _parse_json_object(cls, content: str) -> Dict[str, Any]:
        """Parse a JSON object while tolerating harmless wrappers, never repairing truncated JSON."""
        s = cls._strip_code_fence(content)
        try:
            obj = json.loads(s)
            if not isinstance(obj, dict):
                raise ValueError("LLM output is not a JSON object")
            return obj
        except json.JSONDecodeError as first:
            # Some servers/models may prepend a short non-JSON token despite the prompt.
            start = s.find("{")
            if start < 0:
                raise first
            dec = json.JSONDecoder()
            try:
                obj, _ = dec.raw_decode(s[start:])
            except json.JSONDecodeError:
                raise first
            if not isinstance(obj, dict):
                raise ValueError("Recovered LLM output is not a JSON object")
            return obj

    @staticmethod
    def _sanitize_fact(fact: Dict[str, Any], idx: int) -> Dict[str, Any]:
        allowed={"fact_id","entity","metric","value","surface_value","unit","currency","time",
                 "negation","comparison","direction","term","ticker","acronym","confidence"}
        out={k:v for k,v in fact.items() if k in allowed and v is not None}
        out["fact_id"] = f"H{idx}"
        v=out.get("negation", False)
        out["negation"] = v.strip().lower() in {"true","1","yes"} if isinstance(v,str) else bool(v)
        if "value" in out:
            try: out["value"] = float(out["value"])
            except (TypeError,ValueError): out.pop("value",None)
        try: out["confidence"] = min(1.0,max(0.0,float(out.get("confidence",1.0))))
        except (TypeError,ValueError): out["confidence"] = 1.0
        for k in ("comparison","direction"):
            if out.get(k) in {"","none","null","None"}: out.pop(k,None)
        return out

    def _request(self, text: str, language: str, compact_retry: bool=False) -> Dict[str, Any]:
        system = SYSTEM_PROMPT.format(max_facts=self.max_facts)
        if compact_retry:
            system += "\nRETRY MODE: The previous response was invalid. Return a SHORT valid JSON object only."
        payload = {
            "model": self.model,
            "messages": [
                {"role":"system", "content":system},
                {"role":"user", "content":USER_TEMPLATE.format(language=self._language_name(language), text=text)},
            ],
            "temperature": self.temperature,
            "top_p": 1.0,
            "max_tokens": self.max_tokens,
            "response_format": {"type":"json_object"},
        }
        # vLLM/Qwen3: prevent hidden/visible reasoning from consuming the output budget.
        if self.disable_thinking:
            payload["chat_template_kwargs"] = {"enable_thinking": False}

        req=urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload,ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type":"application/json","Authorization":f"Bearer {self.api_key}"},
            method="POST")
        with urllib.request.urlopen(req,timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def extract(self, text: str, language: str="en", reference_facts=None) -> List[Dict[str,Any]]:
        #import ipdb; ipdb.set_trace()
        del reference_facts  # preserve FER-Auto independence
        text = (text or "").strip()
        if not text:
            return []
        last_error=None
        for attempt in range(self.retries+1):
            content=""
            finish_reason=None
            try:
                response=self._request(text,language,compact_retry=(attempt>0))
                choice=response["choices"][0]
                finish_reason=choice.get("finish_reason")
                content=choice["message"].get("content") or ""
                if finish_reason == "length":
                    raise ValueError(f"LLM output truncated (finish_reason=length, chars={len(content)})")
                obj=self._parse_json_object(content)
                facts=obj.get("facts",[])
                if not isinstance(facts,list):
                    raise ValueError("LLM response field 'facts' is not a list")
                facts=facts[:self.max_facts]
                return [self._sanitize_fact(f,i+1) for i,f in enumerate(facts) if isinstance(f,dict)]
            except (urllib.error.URLError,urllib.error.HTTPError,KeyError,IndexError,
                    json.JSONDecodeError,ValueError) as exc:
                last_error=exc
                if self.debug:
                    preview=content[:1200].replace("\n","\\n")
                    print(f"[LLM extractor retry {attempt+1}/{self.retries+1}] lang={language} "
                          f"finish_reason={finish_reason} chars={len(content)} error={exc} content={preview}")
                if attempt < self.retries:
                    time.sleep(1.5*(attempt+1))
        raise RuntimeError(f"LLM financial fact extraction failed after {self.retries+1} attempts: {last_error}")
