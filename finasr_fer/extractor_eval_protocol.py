import re
from .alignment import align_facts
from .normalization import value_distance, normalize_text
from .parser import FinancialFactExtractor

ABS_TIME_RE=re.compile(r"^(?:FY)?20\d{2}(?:Q[1-4])?$",re.I)

def _canon_time(x):
    if x is None:return None
    s=normalize_text(str(x)).replace(" ","").upper()
    if s.startswith("FY"):s=s[2:]
    return s

def _eq(a,b):
    if a is None or b is None:return a is b
    return normalize_text(str(a))==normalize_text(str(b))

def _value_eq(a,b):
    return value_distance(a,b)<1e-6

def evaluate_extractor_protocol(samples, extractor=None):
    """
    Publication-oriented evaluation for partially annotated synthetic references.

    Reports:
    1) annotated-fact recovery for Entity / Metric / Value
    2) Core Fact recovery = entity+metric+value
    3) Absolute Time recovery only for gold absolute fiscal times
    4) Time-scoped Core Fact recovery on the same reliable subset

    Unmatched extra hypothesis facts are NOT counted as FP because the supplied
    financial_facts annotations are known to be non-exhaustive.
    """
    ext=extractor or FinancialFactExtractor()
    stat={k:{"correct":0,"total":0} for k in
          ["entity","metric","value","core_fact","absolute_time","time_scoped_core_fact"]}
    details=[]
    for s in samples:
        rf=s.get("financial_facts",[])
        hf=ext.extract(s.get("text") or s.get("reference_text") or "",s.get("language","en"))
        ali=align_facts(rf,hf)
        matched={p["ref_index"]:p["hyp_index"] for p in ali["pairs"]}
        for i,r in enumerate(rf):
            h=hf[matched[i]] if i in matched else {}
            eok=(r.get("entity") is None) or _eq(r.get("entity"),h.get("entity"))
            mok=(r.get("metric") is None) or _eq(r.get("metric"),h.get("metric"))
            vok=(r.get("value") is None) or _value_eq(r.get("value"),h.get("value"))
            core=eok and mok and vok

            for k,exists,ok in [
                ("entity",r.get("entity") is not None,eok),
                ("metric",r.get("metric") is not None,mok),
                ("value",r.get("value") is not None,vok),
                ("core_fact",True,core),
            ]:
                if exists:
                    stat[k]["total"]+=1
                    stat[k]["correct"]+=int(ok)

            gt=r.get("time")
            if gt is not None and ABS_TIME_RE.match(str(gt).replace(" ","")):
                tok=_canon_time(gt)==_canon_time(h.get("time"))
                stat["absolute_time"]["total"]+=1
                stat["absolute_time"]["correct"]+=int(tok)
                stat["time_scoped_core_fact"]["total"]+=1
                stat["time_scoped_core_fact"]["correct"]+=int(core and tok)

        details.append({"id":s.get("id"),"num_gold":len(rf),"num_hyp":len(hf),"alignment_cost":ali["cost"]})
    metrics={k:{"accuracy":v["correct"]/max(1,v["total"]),**v} for k,v in stat.items()}
    return {"metrics":metrics,"samples":details}
