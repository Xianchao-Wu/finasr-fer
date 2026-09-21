"""Transcript-level raw and normalized error metrics.

This module is deliberately separate from finasr_fer.normalization so that
FER v0.7.1/v0.8 APIs (normalize_text, value_distance, etc.) remain untouched.

Metrics:
  EN    : WER, WER-N
  ZH/JA : CER, CER-N

-N uses conservative deterministic surface normalization. It is NOT the
financial-semantic normalization used by FER v0.8.
"""
from __future__ import annotations
import re
import unicodedata
from typing import Iterable, Tuple

# Characters treated as orthographic punctuation/separators by -N.
_PUNCT = re.compile(
    r"""[\s!"#&'()*+,\-/:;<=>?@\[\]^_`{|}~"""
    r"""，。！？、；：“”‘’（）【】《》〈〉…—・･「」『』〔〕［］｛｝]+"""
)

def _nfkc(text: str) -> str:
    return unicodedata.normalize("NFKC", str(text or ""))

def normalize_transcript(text: str, language: str, normalized: bool = False) -> str:
    """Normalize transcript for raw or -N scoring.

    Raw:
      * NFKC for stable Unicode representation.
      * remove whitespace for character-based ZH/JA scoring.
      * collapse whitespace for English word scoring.

    -N additionally:
      * case-fold;
      * remove punctuation/separators;
      * normalize unambiguous percent/currency surface aliases.

    We intentionally avoid aggressive free-form CJK number-word conversion.
    """
    lang = language.lower()
    if lang not in {"en", "zh", "ja"}:
        raise ValueError(f"unsupported language: {language}")

    s = _nfkc(text)

    if not normalized:
        if lang in {"zh", "ja"}:
            return re.sub(r"\s+", "", s)
        return " ".join(s.split())

    s = s.casefold()

    # Conservative, unambiguous aliases.
    s = re.sub(r"パーセント|percent", "%", s, flags=re.I)
    s = re.sub(r"日本円|円", "¥", s)
    s = re.sub(r"米ドル|ドル", "$", s)

    # Preserve decimal points only when they occur between digits.
    s = re.sub(r"(?<!\d)\.", "", s)
    s = re.sub(r"\.(?!\d)", "", s)

    if lang in {"zh", "ja"}:
        return _PUNCT.sub("", s)

    s = _PUNCT.sub(" ", s)
    return " ".join(s.split())


def edit_distance(a, b) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(
                cur[-1] + 1,
                prev[j] + 1,
                prev[j - 1] + (x != y),
            ))
        prev = cur
    return prev[-1]


def error_counts(reference: str, hypothesis: str, language: str,
                 normalized: bool = False) -> Tuple[int, int]:
    ref = normalize_transcript(reference, language, normalized)
    hyp = normalize_transcript(hypothesis, language, normalized)

    if language.lower() == "en":
        ref_units, hyp_units = ref.split(), hyp.split()
    else:
        ref_units, hyp_units = list(ref), list(hyp)

    return edit_distance(ref_units, hyp_units), len(ref_units)


def corpus_error_rate(pairs: Iterable[Tuple[str, str]], language: str,
                      normalized: bool = False) -> float:
    errors = total = 0
    for reference, hypothesis in pairs:
        e, n = error_counts(reference, hypothesis, language, normalized)
        errors += e
        total += n
    return errors / total if total else float("nan")


def compute_transcript_metrics(pairs: Iterable[Tuple[str, str]],
                               language: str) -> dict:
    pairs = list(pairs)
    raw = corpus_error_rate(pairs, language, normalized=False)
    norm = corpus_error_rate(pairs, language, normalized=True)

    if language.lower() == "en":
        return {
            "wer": raw,
            "wer_normalized": norm,
            "wer_pct": 100.0 * raw,
            "wer_normalized_pct": 100.0 * norm,
        }

    return {
        "cer": raw,
        "cer_normalized": norm,
        "cer_pct": 100.0 * raw,
        "cer_normalized_pct": 100.0 * norm,
    }
