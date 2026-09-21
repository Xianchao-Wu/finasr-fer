from finasr_fer.transcript_metrics import (
    normalize_transcript,
    compute_transcript_metrics,
    error_counts,
)


# ============================================================
# 1. Unicode / case normalization
# ============================================================

def test_nfkc_width_and_case_for_normalized_metric():
    """Full-width Latin characters should become ASCII and lowercase."""
    assert normalize_transcript(
        "ＳＴＲＯＮＧ", "zh", True
    ) == "strong"


def test_fullwidth_digits_are_normalized():
    """Full-width financial digits should become ASCII digits."""
    assert normalize_transcript(
        "売上高は１２３４円", "ja", True
    ) == "売上高は1234¥"


# ============================================================
# 2. Percent normalization
# ============================================================

def test_japanese_percent_alias():
    """Japanese パーセント and % should be equivalent."""
    assert normalize_transcript(
        "8.4パーセント", "ja", True
    ) == "8.4%"


def test_fullwidth_percent_and_decimal():
    """Full-width digits, decimal point and percent sign are normalized."""
    assert normalize_transcript(
        "８．４％", "ja", True
    ) == "8.4%"


def test_percent_surface_difference_disappears_in_cer_n():
    pairs = [
        (
            "利益は8.4パーセント増加",
            "利益は8.4%増加",
        )
    ]

    m = compute_transcript_metrics(pairs, "ja")

    assert m["cer_normalized"] == 0.0
    assert m["cer_normalized"] <= m["cer"]


# ============================================================
# 3. Currency normalization
# ============================================================

def test_japanese_currency_alias():
    """Japanese 円 should be normalized to the canonical yen symbol."""
    assert normalize_transcript(
        "100円", "ja", True
    ) == "100¥"


def test_japanese_currency_full_name_alias():
    assert normalize_transcript(
        "100日本円", "ja", True
    ) == "100¥"


def test_dollar_alias():
    assert normalize_transcript(
        "100米ドル", "ja", True
    ) == "100$"


# ============================================================
# 4. Decimal-point protection
# ============================================================

def test_decimal_point_is_preserved():
    """
    Decimal points inside numbers carry financial meaning and
    must never be removed.
    """
    assert normalize_transcript(
        "8.4%", "ja", True
    ) == "8.4%"


def test_financial_decimal_is_preserved():
    assert normalize_transcript(
        "ROEは12.6%", "ja", True
    ) == "roeは12.6%"


def test_decimal_financial_error_remains():
    """
    8.4% -> 8.5% is a real ASR error and normalization must
    not erase it.
    """
    pairs = [
        (
            "利益率は8.4%",
            "利益率は8.5%",
        )
    ]

    m = compute_transcript_metrics(pairs, "ja")

    assert m["cer_normalized"] > 0.0


def test_decimal_shift_error_remains():
    """
    8.4% -> 84% must remain an error.
    This guards against accidentally deleting decimal points.
    """
    pairs = [
        (
            "利益率は8.4%",
            "利益率は84%",
        )
    ]

    m = compute_transcript_metrics(pairs, "ja")

    assert m["cer_normalized"] > 0.0


# ============================================================
# 5. Sentence punctuation
# ============================================================

def test_sentence_period_is_removed():
    """
    A sentence-final period is orthographic and should not
    affect WER-N.
    """
    assert normalize_transcript(
        "Revenue was STRONG.",
        "en",
        True,
    ) == "revenue was strong"


def test_english_case_and_punctuation_disappear_in_wer_n():
    pairs = [
        (
            "Revenue was STRONG.",
            "revenue was strong",
        )
    ]

    m = compute_transcript_metrics(pairs, "en")

    assert m["wer_normalized"] == 0.0


def test_english_question_mark_disappears():
    pairs = [
        (
            "Revenue increased?",
            "revenue increased",
        )
    ]

    m = compute_transcript_metrics(pairs, "en")

    assert m["wer_normalized"] == 0.0


# ============================================================
# 6. Full-width financial expressions
# ============================================================

def test_full_width_financial_expression_disappears_in_cer_n():
    pairs = [
        (
            "売上高は２７７０２９円",
            "売上高は277029円",
        )
    ]

    m = compute_transcript_metrics(pairs, "ja")

    assert m["cer_normalized"] == 0.0


def test_full_width_percentage_disappears_in_cer_n():
    pairs = [
        (
            "利益率は１２．６％",
            "利益率は12.6%",
        )
    ]

    m = compute_transcript_metrics(pairs, "ja")

    assert m["cer_normalized"] == 0.0


# ============================================================
# 7. Genuine financial errors must remain
# ============================================================

def test_financial_value_error_remains():
    """
    Normalization must never hide a changed financial value.
    """
    pairs = [
        (
            "売上高は100円",
            "売上高は200円",
        )
    ]

    m = compute_transcript_metrics(pairs, "ja")

    assert m["cer_normalized"] > 0.0


def test_percentage_value_error_remains():
    pairs = [
        (
            "ROEは12.6%",
            "ROEは12.8%",
        )
    ]

    m = compute_transcript_metrics(pairs, "ja")

    assert m["cer_normalized"] > 0.0


def test_english_financial_value_error_remains():
    pairs = [
        (
            "Revenue increased by 12.6%.",
            "Revenue increased by 126%.",
        )
    ]

    m = compute_transcript_metrics(pairs, "en")

    assert m["wer_normalized"] > 0.0


# ============================================================
# 8. Raw vs normalized metrics
# ============================================================

def test_normalized_cer_not_worse_for_orthographic_variation():
    pairs = [
        (
            "利益率は８．４パーセント。",
            "利益率は8.4%",
        )
    ]

    m = compute_transcript_metrics(pairs, "ja")

    assert m["cer_normalized"] <= m["cer"]


def test_normalized_wer_not_worse_for_case_and_punctuation():
    pairs = [
        (
            "Revenue Was STRONG.",
            "revenue was strong",
        )
    ]

    m = compute_transcript_metrics(pairs, "en")

    assert m["wer_normalized"] <= m["wer"]


# ============================================================
# 9. error_counts sanity checks
# ============================================================

def test_identical_japanese_has_zero_errors():
    errors, ref_len = error_counts(
        "売上高は100円",
        "売上高は100円",
        "ja",
        normalized=True,
    )

    assert errors == 0
    assert ref_len > 0


def test_identical_english_has_zero_errors():
    errors, ref_len = error_counts(
        "Revenue increased",
        "Revenue increased",
        "en",
        normalized=True,
    )

    assert errors == 0
    assert ref_len == 2
