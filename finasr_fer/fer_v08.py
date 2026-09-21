"""FER v0.8: reference-anchored Structured Financial Error Rate.

This module is intentionally additive: it can be committed beside the existing
v0.7.1 implementation without breaking the v0.7.1 tagged behavior.

v0.8 changes:
  * extract canonical facts only from the reference;
  * judge each fixed reference fact against the ASR hypothesis;
  * categorical severity -> deterministic numeric scoring;
  * active-field normalization;
  * explicit unsupported-claim (hallucination) penalty;
  * extraction failure is retryable and can be marked invalid instead of
    silently becoming FER=0 or FER=1;
  * multilingual surface equivalence is handled in the judge rubric.

Final score:
    E_ref = sum_i w_i e_i / sum_i w_i
    H     = min(1, sum_j u_j h_j / (sum_i w_i + eps))
    FER   = 1 - (1 - E_ref) * (1 - gamma * H)
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
import json
import math
import re
import unicodedata
import requests

FER_VERSION = "0.8"

FIELD_WEIGHTS = {
    "entity": 1.0,
    "metric": 1.0,
    "value": 2.5,
    "unit": 1.5,
    "currency": 1.5,
    "time": 1.5,
    "negation": 2.5,
    "comparison": 2.5,
    "direction": 2.0,
    "binding": 2.5,
}

SEVERITY_TO_ERROR = {
    "preserved": 0.00,
    "minor": 0.25,
    "partial": 0.50,
    "major": 0.75,
    "missing": 1.00,
    "contradicted": 1.00,
}

REFERENCE_PROMPT = r"""You are the reference-side financial fact annotator for FER v0.8.

Extract ONLY financially meaningful, independently falsifiable propositions
explicitly supported by the REFERENCE transcript.

Use this canonical schema:
{
  "facts": [{
    "fact_id": "F1",
    "entity": "",
    "metric": "",
    "value": "",
    "unit": "",
    "currency": "",
    "time": "",
    "negation": "",
    "comparison": "",
    "direction": "",
    "binding": "",
    "importance": 2.0
  }]
}

Rules:
- One independently falsifiable financial proposition = one fact.
- Do not split a single proposition merely because it contains entity, metric,
  value, unit, currency, and time.
- Do not infer unsupported information.
- importance is 1.0, 2.0, or 3.0.
- Use empty strings for unavailable fields.
- Translation, transliteration, case, full-width/half-width, abbreviations,
  simplified/traditional Chinese, Japanese numeral formatting, and equivalent
  financial surface forms must not create separate facts.
Return JSON only.
"""

JUDGE_PROMPT = r"""You are the reference-anchored FER v0.8 judge.

You receive:
1) REFERENCE transcript,
2) fixed REFERENCE facts,
3) ASR HYPOTHESIS.

Do NOT independently create a new hypothesis fact schema. For EACH supplied
reference fact, judge whether each active field is preserved.

Allowed labels only:
  preserved, minor, partial, major, missing, contradicted

Meaning:
  preserved    = semantically equivalent
  minor        = surface distortion with essentially preserved financial meaning
  partial      = partial information loss or ambiguity
  major        = substantial financial meaning distortion
  missing      = information absent
  contradicted = hypothesis states incompatible financial information

Equivalence rules (normally preserved):
- STRONG == strong;
- full-width == half-width;
- simplified Chinese == traditional Chinese when meaning is unchanged;
- 8.4% == 百分之八点四 == 8.4パーセント;
- equivalent Arabic/Chinese/Japanese numeral expressions;
- unambiguous abbreviation/full name;
- faithful translation/transliteration;
- equivalent date/currency/number formatting.

Numerical rule:
If the normalized numeric value changes, do NOT hide it as a surface variation.
Magnitude, sign, percentage/basis-point, currency and unit changes must be
judged according to their financial effect.

Also return genuinely unsupported NEW financial claims from the hypothesis.
Do not call paraphrases, translations, formatting changes, or restatements new.

Return JSON only:
{
  "judgments": [{
    "fact_id": "F1",
    "entity": "preserved",
    "metric": "preserved",
    "value": "preserved",
    "unit": "preserved",
    "currency": "preserved",
    "time": "preserved",
    "negation": "preserved",
    "comparison": "preserved",
    "direction": "preserved",
    "binding": "preserved",
    "reason": ""
  }],
  "extra_hypothesis_facts": [{
    "description": "",
    "severity": "major",
    "importance": 2.0
  }]
}
"""


def normalize_surface(s: Any) -> str:
    """Conservative Unicode/case/space normalization for diagnostics."""
    s = unicodedata.normalize("NFKC", str(s or "")).casefold()
    s = re.sub(r"\s+", "", s)
    return s


def _json_object(text: str) -> Dict[str, Any]:
    text = str(text).strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        a, b = text.find("{"), text.rfind("}")
        if a < 0 or b <= a:
            raise
        obj = json.loads(text[a:b+1])
    if not isinstance(obj, dict):
        raise ValueError("LLM response is not a JSON object")
    return obj


class OpenAICompatibleLLM:
    def __init__(self, base_url: str, model: Optional[str] = None,
                 timeout: int = 180):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        if model is None:
            r = requests.get(self.base_url + "/models", timeout=30)
            r.raise_for_status()
            model = r.json()["data"][0]["id"]
        self.model = model

    def json(self, system: str, user: str, max_tokens: int = 3072) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.0,
            "max_tokens": max_tokens,
        }
        r = requests.post(self.base_url + "/chat/completions",
                          json=payload, timeout=self.timeout)
        r.raise_for_status()
        return _json_object(r.json()["choices"][0]["message"]["content"])


def _importance(x: Any) -> float:
    try:
        return max(1.0, min(3.0, float(x)))
    except Exception:
        return 2.0


def extract_reference_facts(reference: str, llm: OpenAICompatibleLLM,
                            retries: int = 2) -> List[Dict[str, Any]]:
    last = None
    for _ in range(retries + 1):
        try:
            obj = llm.json(REFERENCE_PROMPT, "REFERENCE:\n" + reference)
            facts = obj.get("facts", [])
            if not isinstance(facts, list):
                raise ValueError("facts is not a list")
            out = []
            for i, f in enumerate(facts, 1):
                if not isinstance(f, dict):
                    continue
                g = {k: str(f.get(k, "") or "") for k in
                     ("entity","metric","value","unit","currency","time",
                      "negation","comparison","direction","binding")}
                g["fact_id"] = str(f.get("fact_id") or f"F{i}")
                g["importance"] = _importance(f.get("importance", 2.0))
                if any(g[k].strip() for k in FIELD_WEIGHTS):
                    out.append(g)
            return out
        except Exception as e:
            last = e
    raise RuntimeError(f"reference extraction failed after retries: {last}")


def judge(reference: str, hypothesis: str, facts: List[Dict[str, Any]],
          llm: OpenAICompatibleLLM) -> Dict[str, Any]:
    user = json.dumps({
        "reference": reference,
        "reference_facts": facts,
        "hypothesis": hypothesis,
    }, ensure_ascii=False, indent=2)
    return llm.json(JUDGE_PROMPT, user)


def score(reference_facts: List[Dict[str, Any]],
          judgment: Dict[str, Any],
          gamma: float = 0.5,
          eps: float = 1e-12) -> Tuple[float, Dict[str, Any]]:
    js = judgment.get("judgments", [])
    if not isinstance(js, list):
        js = []
    by_id = {str(j.get("fact_id")): j for j in js
             if isinstance(j, dict) and j.get("fact_id") is not None}

    ref_num = 0.0
    ref_den = 0.0
    per_fact = []

    for f in reference_facts:
        fid = str(f["fact_id"])
        j = by_id.get(fid)
        missing_judgment = j is None
        if j is None:
            j = {}

        active = [k for k in FIELD_WEIGHTS if str(f.get(k, "") or "").strip()]
        denom = sum(FIELD_WEIGHTS[k] for k in active)
        num = 0.0
        field_scores = {}

        for k in FIELD_WEIGHTS:
            if k not in active:
                label, err = "inactive", 0.0
            elif missing_judgment:
                label, err = "missing", 1.0
            else:
                label = str(j.get(k, "missing")).strip().lower()
                err = SEVERITY_TO_ERROR.get(label, 1.0)
            field_scores[k] = {"label": label, "error": err}
            if k in active:
                num += FIELD_WEIGHTS[k] * err

        e_i = num / denom if denom else 0.0
        w_i = _importance(f.get("importance", 2.0))
        ref_num += w_i * e_i
        ref_den += w_i
        per_fact.append({
            "fact_id": fid, "importance": w_i, "error": e_i,
            "fields": field_scores, "reason": j.get("reason", ""),
            "missing_judgment": missing_judgment,
        })

    # No extracted reference facts must never silently become a valid zero.
    if not reference_facts:
        raise ValueError("no reference facts; mark sample extraction_failed/NaN")

    e_ref = ref_num / max(ref_den, eps)

    extras = judgment.get("extra_hypothesis_facts", [])
    if not isinstance(extras, list):
        extras = []
    hall_num = 0.0
    scored_extras = []
    for x in extras:
        if not isinstance(x, dict):
            continue
        label = str(x.get("severity", "major")).lower()
        h = SEVERITY_TO_ERROR.get(label, 0.75)
        u = _importance(x.get("importance", 2.0))
        hall_num += u * h
        scored_extras.append({
            "description": str(x.get("description", "")),
            "severity": label, "error": h, "importance": u
        })

    H = min(1.0, hall_num / max(ref_den, eps))
    fer = 1.0 - (1.0 - e_ref) * (1.0 - gamma * H)
    fer = max(0.0, min(1.0, fer))

    return fer, {
        "fer_version": FER_VERSION,
        "E_ref": e_ref,
        "H": H,
        "gamma": gamma,
        "reference_weight": ref_den,
        "per_fact": per_fact,
        "extra_hypothesis_facts": scored_extras,
    }


def evaluate_pair(reference: str, hypothesis: str,
                  llm: OpenAICompatibleLLM,
                  gamma: float = 0.5,
                  retries: int = 2) -> Dict[str, Any]:
    try:
        facts = extract_reference_facts(reference, llm, retries=retries)
        if not facts:
            # Retry once with an explicit reminder before declaring invalid.
            reminder = (
                REFERENCE_PROMPT +
                "\nIMPORTANT: Re-check carefully for financial entities, rankings, "
                "rates, amounts, definitions, metrics, dates, comparisons and "
                "financial relations. Do not return an empty list if any explicit "
                "financial proposition exists."
            )
            obj = llm.json(reminder, "REFERENCE:\n" + reference)
            facts = obj.get("facts", [])
            if not facts:
                return {
                    "fer": None, "fer_version": FER_VERSION,
                    "fer_status": "reference_extraction_failed",
                    "reference_facts_v08": [],
                }
            # canonical cleanup via a minimal normalization pass
            cleaned = []
            for i, f in enumerate(facts, 1):
                if not isinstance(f, dict):
                    continue
                g = {k: str(f.get(k, "") or "") for k in FIELD_WEIGHTS}
                g["fact_id"] = str(f.get("fact_id") or f"F{i}")
                g["importance"] = _importance(f.get("importance", 2.0))
                if any(g[k].strip() for k in FIELD_WEIGHTS):
                    cleaned.append(g)
            facts = cleaned
        if not facts:
            return {
                "fer": None, "fer_version": FER_VERSION,
                "fer_status": "reference_extraction_failed",
                "reference_facts_v08": [],
            }

        j = judge(reference, hypothesis, facts, llm)
        fer, details = score(facts, j, gamma=gamma)
        return {
            "fer": fer,
            "fer_version": FER_VERSION,
            "fer_status": "ok",
            "reference_facts_v08": facts,
            "fer_v08_judgment": j,
            "fer_v08_details": details,
        }
    except Exception as e:
        return {
            "fer": None, "fer_version": FER_VERSION,
            "fer_status": "error",
            "fer_error": repr(e),
        }
