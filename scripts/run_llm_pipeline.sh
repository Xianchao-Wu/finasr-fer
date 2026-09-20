#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/run_llm_pipeline.sh refs.jsonl hyps.jsonl results.jsonl
REFS="${1:?references JSONL required}"
HYPS="${2:?hypotheses JSONL required}"
OUT="${3:-fer_v07_qwen3_results.jsonl}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000/v1}"
MODEL="${SERVED_NAME:-qwen3-financial-extractor}"

python scripts/run_fer_v07_llm.py \
  --references "$REFS" \
  --hypotheses "$HYPS" \
  --output "$OUT" \
  --base-url "$BASE_URL" \
  --model "$MODEL"
