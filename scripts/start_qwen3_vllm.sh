#!/usr/bin/env bash
set -euo pipefail

# Recommended high-quality open-source extractor model.
MODEL="${MODEL:-Qwen/Qwen3-30B-A3B-Instruct-2507}"
SERVED_NAME="${SERVED_NAME:-qwen3-financial-extractor}"
PORT="${PORT:-8000}"
TP="${TP:-8}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-32768}"
GPU_MEM="${GPU_MEM:-0.50}"
HF_CACHE="${HF_CACHE:-$HOME/.cache/huggingface}"

# Qwen publishes this model under Apache-2.0 and documents vLLM serving.
# On an 8xA100-80GB machine, TP=2 is a reasonable default; increase TP if desired.
docker run --rm --gpus all \
  --ipc=host \
  --shm-size=32g \
  -p "${PORT}:8000" \
  -v "${HF_CACHE}:/root/.cache/huggingface" \
  ${HF_TOKEN:+-e HF_TOKEN="$HF_TOKEN"} \
  vllm/vllm-openai:latest \
  --model "$MODEL" \
  --served-model-name "$SERVED_NAME" \
  --tensor-parallel-size "$TP" \
  --max-model-len "$MAX_MODEL_LEN" \
  --gpu-memory-utilization "$GPU_MEM" \
  --dtype auto
