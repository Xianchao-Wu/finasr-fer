# Changelog

## v0.7.0
- Reformulated FER with explicit fact-level normalization and saturation:
  `ell_ij = min(1, L_ij / D_i)`.
- Final FER is provably bounded in `[0,1]`; final clamp is a numerical safeguard only.
- Added per-fact `raw_fact_loss`, `active_weight_mass`, `normalized_fact_loss`, and `bounded_fact_loss` to results.
- Added top-level `bounded_numerator` and `total_information_mass` diagnostics.
- Added `LLMFinancialFactExtractor` using an OpenAI-compatible chat-completions endpoint.
- Added a strict multilingual financial-fact extraction prompt with numeric, unit/currency, temporal, binding, negation, comparison, and direction normalization rules.
- Added Qwen3/vLLM startup and batch FER scripts.

## v0.6.0
- Spurious financial fact penalty.
- Temporal grounding and operator coverage improvements.
- Metric/value binding and derived change/growth improvements.
