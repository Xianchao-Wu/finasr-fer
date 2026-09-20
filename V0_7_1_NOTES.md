# FER v0.7.1 robustness update

- Qwen3 thinking is disabled by default for extraction.
- LLM output is constrained to short JSON-only extraction (default max_tokens=1536, max_facts=30).
- `finish_reason=length` is detected explicitly instead of surfacing as a confusing JSON error.
- JSON parsing tolerates code fences / a short prefix but does not silently repair truncated JSON.
- Retry requests use an additional compact-output instruction.
- Dataset-level FER uses information-mass aggregation: sum bounded numerator / sum information mass.
- Macro utterance FER remains available as `fer_macro`.
