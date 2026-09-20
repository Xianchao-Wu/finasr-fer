from .alignment import align_facts
from .normalization import value_distance, normalize_text
from .parser import FinancialFactExtractor

def _canon_time(x):
    if x is None:return None
    s=normalize_text(str(x)).replace(" ","").upper()
    if s.startswith("FY"):s=s[2:]
    return s

def _eq(a,b,key=None):
    if a is None or b is None:return a is b
    if key=="time":return _canon_time(a)==_canon_time(b)
    return normalize_text(str(a))==normalize_text(str(b))

def evaluate_extractor_gold_covered(samples, extractor=None):
    ext=extractor or FinancialFactExtractor()
    comps=["entity","metric","value","time","fact"]
    stats={k:{"correct":0,"gold":0} for k in comps}
    for s in samples:
        rf=s.get("financial_facts",[])
        hf=ext.extract(s.get("text") or s.get("reference_text") or "",s.get("language","en"))
        ali=align_facts(rf,hf)
        matched={p["ref_index"]:p["hyp_index"] for p in ali["pairs"]}
        for i,r in enumerate(rf):
            h=hf[matched[i]] if i in matched else {}
            checks={
                "entity":(r.get("entity") is None) or _eq(r.get("entity"),h.get("entity")),
                "metric":(r.get("metric") is None) or _eq(r.get("metric"),h.get("metric")),
                "value":(r.get("value") is None) or value_distance(r.get("value"),h.get("value"))<1e-6,
                "time":(r.get("time") is None) or _eq(r.get("time"),h.get("time"),"time")
            }
            checks["fact"]=all(checks.values())
            for k in comps:
                exists=(k=="fact") or (r.get(k) is not None)
                if exists:
                    stats[k]["gold"]+=1
                    if checks[k]:stats[k]["correct"]+=1
    return {"metrics":{k:{"gold_coverage_accuracy":v["correct"]/max(1,v["gold"]),**v} for k,v in stats.items()}}
