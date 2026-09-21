# FER v0.8 Notes

FER v0.8 replaces independent reference/hypothesis fact extraction with
**reference-anchored preservation evaluation**.

## Why

v0.7.1 can over-penalize semantically equivalent multilingual surface forms
when the LLM independently chooses different schemas or fact granularities for
reference and hypothesis. Examples include `8.4%` vs `百分之八点四`,
full-width vs half-width Japanese numerals, English vs Chinese/Japanese field
labels, capitalization, translation, and paraphrase.

## v0.8 changes

1. Extract fixed canonical facts from the reference only.
2. Judge the hypothesis against those fixed anchors.
3. Use categorical severity labels and deterministic numeric mapping.
4. Normalize each fact over active fields only.
5. Keep the v0.7.1 component emphasis: value/binding/negation/comparison remain
   high-impact fields.
6. Separate unsupported-hypothesis penalty from the reference-loss denominator.
7. Retry empty reference extraction; unresolved extraction failure is invalid
   (`FER = null`) rather than forced to 0 or 1.
8. Preserve FER in [0,1].

## Score

For reference fact i:

    e_i = sum_k lambda_k d_ik / sum_{k in active(i)} lambda_k

    E_ref = sum_i w_i e_i / sum_i w_i

For unsupported hypothesis claims:

    H = min(1, sum_j u_j h_j / (sum_i w_i + eps))

Final:

    FER_v0.8 = 1 - (1 - E_ref) * (1 - gamma H)

Default gamma = 0.5.

## Compatibility

The v0.8 implementation is additive (`finasr_fer/fer_v08.py`) so the tagged
v0.7.1 implementation can remain reproducible.
