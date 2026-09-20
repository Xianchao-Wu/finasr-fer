# finasr-fer v0.7.0

Multilingual Structured Financial Error Rate (FER) toolkit for financial ASR.

## What changed in v0.7

FER is now **explicitly bounded in [0,1] at the fact level**. For a matched reference fact `i` and hypothesis fact `j`, define

- weighted corruption: `L_ij = sum_k lambda_k I_ik E_ijk`
- active information mass: `D_i = sum_k lambda_k I_ik`
- normalized fact corruption: `ell_ij = min(1, L_ij / D_i)`
- bounded contribution: `D_i * ell_ij = min(L_ij, D_i)`

The final score is

`FER = (sum_matched D_i ell_ij + sum_missing D_i + lambda_spur N_spur) / (sum_ref D_i + lambda_spur N_spur)`

which is provably in `[0,1]`. A final numerical clamp is retained only as a safety guard.

## Extraction modes

- **FER-Struct / FER-Oracle:** explicit facts on both sides; isolates the scorer.
- **FER-Auto (rules):** gold reference facts + built-in rule-based hypothesis extractor.
- **FER-Auto (LLM):** gold reference facts + `LLMFinancialFactExtractor`, compatible with an OpenAI-style endpoint such as vLLM serving Qwen3.

The LLM prompt is reference-independent: it receives only the hypothesis transcript and language.

## Qwen3 + vLLM pipeline

Recommended default model: `Qwen/Qwen3-30B-A3B-Instruct-2507`.

Start the server:

```bash
bash scripts/start_qwen3_vllm.sh
```

Then run FER v0.7 over JSONL references and hypotheses:

```bash
bash scripts/run_llm_pipeline.sh references.jsonl hypotheses.jsonl fer_v07_qwen3_results.jsonl
```

Hypotheses JSONL format:

```json
{"id":"sample-001","hypothesis_text":"NVIDIA revenue was $12.6 billion in FY2027 Q1."}
```

The batch output preserves the automatically extracted hypothesis facts for auditability.

## Recommended reporting protocol

Report FER-Struct and FER-Auto separately. If using an LLM extractor, record the exact model revision, inference engine/version, prompt, temperature, and decoding settings. Evaluate extractor quality on a held-out manually annotated set before making end-to-end claims.
