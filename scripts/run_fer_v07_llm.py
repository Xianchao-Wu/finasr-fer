#!/usr/bin/env python3
"""Batch FER v0.7 with Qwen3 hypothesis fact extraction.

References JSONL: each line is a FinASR structured reference object containing
  id, text, language, financial_facts, ...
Hypotheses JSONL: each line contains
  {"id": "...", "hypothesis_text": "..."}
"""
import argparse
import json
from pathlib import Path

from finasr_fer import StructuredFEREvaluator, LLMFinancialFactExtractor
from finasr_fer.io import read_jsonl, read_hypotheses_jsonl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--references", required=True)
    ap.add_argument("--hypotheses", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    ap.add_argument("--model", default="qwen3-financial-extractor")
    ap.add_argument("--api-key", default="EMPTY")
    ap.add_argument("--spurious-fact-weight", type=float, default=2.5)
    args = ap.parse_args()

    extractor = LLMFinancialFactExtractor(
        base_url=args.base_url,
        model=args.model,
        api_key=args.api_key,
        temperature=0.0,
    )
    evaluator = StructuredFEREvaluator(
        extractor=extractor,
        mode="auto",
        spurious_fact_weight=args.spurious_fact_weight,
    )

    refs = read_jsonl(args.references)
    hyps = read_hypotheses_jsonl(args.hypotheses)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n = 0
    fer_sum = 0.0
    with out_path.open("w", encoding="utf-8") as fw:
        for ref in refs:
            sid = ref.get("id")
            if sid not in hyps:
                continue
            result = evaluator.evaluate(ref, hyps[sid], mode="auto")
            fw.write(json.dumps(result, ensure_ascii=False) + "\n")
            n += 1
            fer_sum += result["fer"]
            print(f"[{n}] {sid}: FER={result['fer']:.6f} hyp_facts={result['num_hypothesis_facts']}")

    print(json.dumps({"num_samples": n, "mean_fer": fer_sum / n if n else None,
                      "output": str(out_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
