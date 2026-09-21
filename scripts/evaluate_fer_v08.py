#!/usr/bin/env python3
"""Re-score an existing ASR JSONL with FER v0.8 without rerunning ASR."""
import argparse, json, math
from pathlib import Path
from finasr_fer.fer_v08 import OpenAICompatibleLLM, evaluate_pair

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--base-url", default="http://localhost:8000/v1")
    ap.add_argument("--model", default=None)
    ap.add_argument("--gamma", type=float, default=0.5)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    llm = OpenAICompatibleLLM(args.base_url, args.model)
    src, dst = Path(args.input), Path(args.output)
    rows = [json.loads(x) for x in src.read_text(encoding="utf-8").splitlines() if x.strip()]

    fers = []
    with dst.open("w", encoding="utf-8") as f:
        for i, row in enumerate(rows, 1):
            cached = (
                not args.overwrite and row.get("fer_version") == "0.8"
                and row.get("fer_status") == "ok" and row.get("fer") is not None
            )
            if not cached:
                result = evaluate_pair(
                    str(row.get("reference", row.get("text", ""))),
                    str(row.get("hypothesis", "")),
                    llm, gamma=args.gamma,
                )
                # Remove legacy independent-extraction fields to prevent mixing.
                row.pop("reference_facts", None)
                row.pop("hypothesis_facts", None)
                row.update(result)
            if row.get("fer") is not None:
                fers.append(float(row["fer"]))
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"\r{i}/{len(rows)}", end="", flush=True)

    print()
    print(f"valid FER: {len(fers)}/{len(rows)}")
    if fers:
        print(f"mean FER v0.8: {sum(fers)/len(fers):.6f}")

if __name__ == "__main__":
    main()
