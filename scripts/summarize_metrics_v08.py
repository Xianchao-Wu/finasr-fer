#!/usr/bin/env python3
"""Summarize raw/-N transcript error, SemDist and FER from prediction JSONL."""
import argparse
import json
from pathlib import Path

from finasr_fer.transcript_metrics import compute_transcript_metrics


def main():
    p = argparse.ArgumentParser()
    p.add_argument("jsonl")
    p.add_argument("--language", required=True, choices=["en", "zh", "ja"])
    p.add_argument("--fer-version", default="0.8",
                   help="FER version to include; default: 0.8")
    args = p.parse_args()

    rows = [
        json.loads(line)
        for line in Path(args.jsonl).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    pairs = [
        (
            str(r.get("reference", r.get("text", ""))),
            str(r.get("hypothesis", "")),
        )
        for r in rows
    ]
    m = compute_transcript_metrics(pairs, args.language)

    sem = [float(r["semdist"]) for r in rows if r.get("semdist") is not None]
    fer = [
        float(r["fer"])
        for r in rows
        if str(r.get("fer_version", "")) == args.fer_version
        and r.get("fer") is not None
    ]

    print(f"N: {len(rows)}")
    if args.language == "en":
        print(f"WER:   {m['wer_pct']:.4f}%")
        print(f"WER-N: {m['wer_normalized_pct']:.4f}%")
    else:
        print(f"CER:   {m['cer_pct']:.4f}%")
        print(f"CER-N: {m['cer_normalized_pct']:.4f}%")

    print(f"SemDist: {sum(sem)/len(sem):.6f}" if sem else "SemDist: NA")
    print(
        f"FER-v{args.fer_version}: {sum(fer)/len(fer):.6f}"
        if fer else f"FER-v{args.fer_version}: NA"
    )
    print(f"Valid SemDist: {len(sem)}/{len(rows)}")
    print(f"Valid FER: {len(fer)}/{len(rows)}")


if __name__ == "__main__":
    main()
