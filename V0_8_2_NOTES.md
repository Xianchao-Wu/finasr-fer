# FER v0.8.2 hotfix

This is an additive compatibility hotfix for a repository that already contains
the FER v0.8 commit.

## Important

It does **not** replace or modify:

- `finasr_fer/normalization.py`
- `finasr_fer/evaluator.py`
- `finasr_fer/fer_v08.py`
- `finasr_fer/__init__.py`

The previous v0.8.1 draft accidentally reused `normalization.py`, which conflicts
with the v0.7.1 evaluator API (`normalize_text`, `value_distance`). v0.8.2 moves
transcript-level WER/CER normalization into an independent module:

`finasr_fer/transcript_metrics.py`

## Metrics

- EN: WER, WER-N, SemDist, FER v0.8
- ZH/JA: CER, CER-N, SemDist, FER v0.8

`-N` is deterministic transcript-surface normalization and remains conceptually
separate from FER v0.8's reference-anchored financial-semantic evaluation.

## Normalized transcript operations

- Unicode NFKC
- case folding
- punctuation / whitespace normalization
- `percent` / `パーセント` -> `%`
- `円` / `日本円` -> `¥`
- `ドル` / `米ドル` -> `$`

Aggressive free-form CJK number-word conversion is deliberately excluded.
