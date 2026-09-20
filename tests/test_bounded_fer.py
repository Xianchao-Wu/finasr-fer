import random
from finasr_fer import StructuredFEREvaluator


def test_fer_is_bounded_for_complete_mismatch():
    ref = {
        "id": "x", "language": "en", "text": "NVIDIA revenue was $12.6 billion in FY2027 Q1.",
        "financial_facts": [{
            "fact_id": "F1", "entity": "NVIDIA", "metric": "revenue",
            "value": 12.6e9, "surface_value": "$12.6 billion",
            "unit": "absolute_money", "currency": "USD", "time": "FY2027Q1"
        }]
    }
    hyp_facts = [{
        "fact_id": "H1", "entity": "AMD", "metric": "net income",
        "value": 1.0, "unit": "ratio", "currency": "JPY", "time": "FY2030Q4",
        "negation": True, "comparison": "less_than", "direction": "decrease"
    }]
    r = StructuredFEREvaluator(mode="struct").evaluate(ref, "dummy", hypothesis_facts=hyp_facts)
    assert 0.0 <= r["fer"] <= 1.0
    assert all(0.0 <= x["normalized_fact_loss"] <= 1.0 for x in r["fact_results"])


def test_spurious_facts_approach_one_without_exceeding_one():
    ref = {
        "id": "x", "language": "en", "text": "NVIDIA revenue was $12.6 billion.",
        "financial_facts": [{"fact_id": "F1", "entity": "NVIDIA", "metric": "revenue", "value": 12.6e9}]
    }
    ev = StructuredFEREvaluator(mode="struct")
    for n in (0, 1, 5, 100):
        hyps = [{"fact_id": f"H{i+1}", "entity": f"E{i}", "metric": "revenue", "value": float(i+1)} for i in range(max(1, n+1))]
        r = ev.evaluate(ref, "dummy", hypothesis_facts=hyps)
        assert 0.0 <= r["fer"] <= 1.0


def test_empty_reference_and_no_hypothesis_is_zero():
    ref = {"id": "x", "language": "en", "text": "hello", "financial_facts": []}
    r = StructuredFEREvaluator(mode="struct").evaluate(ref, "hello", hypothesis_facts=[])
    assert r["fer"] == 0.0
