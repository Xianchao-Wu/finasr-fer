from finasr_fer.fer_v08 import score, SEVERITY_TO_ERROR

def _fact():
    return [{
        "fact_id":"F1", "entity":"", "metric":"revenue growth",
        "value":"8.4", "unit":"%", "currency":"", "time":"Q2",
        "negation":"", "comparison":"", "direction":"", "binding":"",
        "importance":2.0
    }]

def test_preserved_is_zero():
    j={"judgments":[{
        "fact_id":"F1","metric":"preserved","value":"preserved",
        "unit":"preserved","time":"preserved"
    }],"extra_hypothesis_facts":[]}
    fer, d=score(_fact(), j)
    assert fer == 0.0

def test_missing_is_one():
    j={"judgments":[{
        "fact_id":"F1","metric":"missing","value":"missing",
        "unit":"missing","time":"missing"
    }],"extra_hypothesis_facts":[]}
    fer, d=score(_fact(), j)
    assert fer == 1.0

def test_hallucination_increases_score_without_diluting_reference_error():
    base={"judgments":[{
        "fact_id":"F1","metric":"preserved","value":"preserved",
        "unit":"preserved","time":"preserved"
    }],"extra_hypothesis_facts":[]}
    extra={**base, "extra_hypothesis_facts":[{
        "description":"unsupported revenue value","severity":"major","importance":2.0
    }]}
    f0,_=score(_fact(),base)
    f1,_=score(_fact(),extra)
    assert f1 > f0

def test_no_reference_facts_is_invalid():
    try:
        score([], {"judgments":[]})
    except ValueError:
        return
    assert False, "empty reference facts must not silently produce FER"
