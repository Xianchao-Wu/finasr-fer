# FER v0.7 regression check

- Unit tests: 3/3 passed.
- Python package compiles successfully.
- LLM extractor interface tested against a local OpenAI-compatible mock endpoint.
- On the existing 120-sample human-severity set using the same rule-based automatic extractor:
  - v0.6 mean FER-Auto: 0.30126220585960445
  - v0.7 mean FER-Auto: 0.30126220585960445
  - maximum absolute per-sample difference: 5.55e-17
  - all v0.7 scores are in [0,1].

The equality is expected because current component errors are already normalized to [0,1]. v0.7 makes the bound explicit at fact level and adds defensive normalization for future scorer extensions.
