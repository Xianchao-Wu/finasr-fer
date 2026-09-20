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

def evaluate_extractor(samples, extractor=None):
    ext=extractor or FinancialFactExtractor()
    counts={k:{"tp":0,"fp":0,"fn":0} for k in ["entity","metric","value","time","fact"]}
    per_sample=[]
    for s in samples:
        rf=s.get("financial_facts",[])
        hf=ext.extract(s.get("text") or s.get("reference_text") or "",s.get("language","en"))
        ali=align_facts(rf,hf)
        for p in ali["pairs"]:
            r=rf[p["ref_index"]];h=hf[p["hyp_index"]]
            comps={
                "entity":(r.get("entity") is None) or _eq(r.get("entity"),h.get("entity")),
                "metric":(r.get("metric") is None) or _eq(r.get("metric"),h.get("metric")),
                "value":(r.get("value") is None) or value_distance(r.get("value"),h.get("value"))<1e-6,
                "time":(r.get("time") is None) or _eq(r.get("time"),h.get("time"),"time")
            }
            comps["fact"]=all(comps.values())
            for k,v in comps.items():
                if v:counts[k]["tp"]+=1
                else:
                    counts[k]["fn"]+=1
                    counts[k]["fp"]+=1
        for _ in ali["unmatched_ref"]:
            for k in counts:counts[k]["fn"]+=1
        for _ in ali["unmatched_hyp"]:
            for k in counts:counts[k]["fp"]+=1
        per_sample.append({"id":s.get("id"),"num_ref":len(rf),"num_hyp":len(hf),"alignment_cost":ali["cost"]})
    metrics={}
    for k,c in counts.items():
        p=c["tp"]/max(1,c["tp"]+c["fp"])
        r=c["tp"]/max(1,c["tp"]+c["fn"])
        f=2*p*r/max(1e-12,p+r)
        metrics[k]={"precision":p,"recall":r,"f1":f,**c}
    return {"metrics":metrics,"samples":per_sample}
