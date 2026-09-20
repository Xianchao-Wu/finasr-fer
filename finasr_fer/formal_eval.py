import math
from collections import defaultdict
from .parser import FinancialFactExtractor
from .alignment import align_facts
from .normalization import normalize_text, value_distance
from .evaluator import StructuredFEREvaluator

UNIT_CANON={
    "basis_point_ratio":"delta","percentage_point":"delta","basis_points":"delta",
    "percentage_points":"delta","ratio":"ratio","absolute_money":"absolute_money",
    "delta":"delta","number":"number","scaled_number":"scaled_number"
}

def canon_unit(x):
    if x in (None,""): return None
    return UNIT_CANON.get(str(x),str(x))

def canon_str(x):
    if x in (None,""): return None
    return normalize_text(str(x))

def canon_time(x):
    if x in (None,""): return None
    s=normalize_text(str(x)).replace(" ","").upper()
    return s[2:] if s.startswith("FY") else s

def eq_value(a,b):
    if a is None or b is None:return a is b
    return value_distance(a,b)<1e-6

def eq_field(k,a,b):
    if k=="value":return eq_value(a,b)
    if k=="unit":return canon_unit(a)==canon_unit(b)
    if k=="time":return canon_time(a)==canon_time(b)
    if k=="negation":return bool(a)==bool(b)
    if k in ("comparison","direction","currency","entity","metric"):
        return canon_str(a)==canon_str(b)
    return a==b

COMP_FIELDS=["entity","metric","value","unit","currency","time"]
CORE_FIELDS=["entity","metric","value"]
FULL_FIELDS=["entity","metric","value","unit","currency","time","negation","comparison","direction"]

def _counts():
    return {k:{"tp":0,"fp":0,"fn":0} for k in COMP_FIELDS+["core_fact","full_fact"]}

def _update(c,refs,hyps,ali):
    for p in ali["pairs"]:
        r,h=refs[p["ref_index"]],hyps[p["hyp_index"]]
        for k in COMP_FIELDS:
            rv,hv=r.get(k),h.get(k)
            if rv in (None,"") and hv in (None,""):continue
            if eq_field(k,rv,hv):c[k]["tp"]+=1
            else:
                if rv not in (None,""):c[k]["fn"]+=1
                if hv not in (None,""):c[k]["fp"]+=1
        core=all(eq_field(k,r.get(k),h.get(k)) for k in CORE_FIELDS)
        full=all(eq_field(k,r.get(k),h.get(k)) for k in FULL_FIELDS)
        if core:c["core_fact"]["tp"]+=1
        else:c["core_fact"]["fn"]+=1;c["core_fact"]["fp"]+=1
        if full:c["full_fact"]["tp"]+=1
        else:c["full_fact"]["fn"]+=1;c["full_fact"]["fp"]+=1
    for ri in ali["unmatched_ref"]:
        r=refs[ri]
        for k in COMP_FIELDS:
            if r.get(k) not in (None,""):c[k]["fn"]+=1
        c["core_fact"]["fn"]+=1;c["full_fact"]["fn"]+=1
    for hi in ali["unmatched_hyp"]:
        h=hyps[hi]
        for k in COMP_FIELDS:
            if h.get(k) not in (None,""):c[k]["fp"]+=1
        c["core_fact"]["fp"]+=1;c["full_fact"]["fp"]+=1

def _prf(c):
    p=c["tp"]/max(1,c["tp"]+c["fp"])
    r=c["tp"]/max(1,c["tp"]+c["fn"])
    f=2*p*r/max(1e-12,p+r)
    return {"precision":p,"recall":r,"f1":f,**c}

def evaluate_samples(samples,extractor=None):
    ext=extractor or FinancialFactExtractor()
    fer_eval=StructuredFEREvaluator()
    overall=_counts()
    langs=defaultdict(_counts)
    fer_by_lang=defaultdict(list)
    operator={l:{k:{"correct":0,"total":0,"positive_correct":0,"positive_total":0}
                 for k in ("negation","comparison","direction")} for l in ("en","zh","ja")}
    binding={l:{"correct":0,"total":0} for l in ("en","zh","ja")}

    for s in samples:
        lang=s["language"]
        refs=[]
        for f in s["financial_facts"]:
            nf=dict(f);nf["unit"]=canon_unit(nf.get("unit"));refs.append(nf)
        hyps=ext.extract(s["text"],lang)
        ali=align_facts(refs,hyps)
        _update(overall,refs,hyps,ali);_update(langs[lang],refs,hyps,ali)
        matched={p["ref_index"]:p["hyp_index"] for p in ali["pairs"]}
        for ri,r in enumerate(refs):
            binding[lang]["total"]+=1
            if ri not in matched:
                for k in operator[lang]:
                    operator[lang][k]["total"]+=1
                    pos=bool(r.get(k)) if k=="negation" else r.get(k) not in (None,"")
                    if pos:operator[lang][k]["positive_total"]+=1
                continue
            h=hyps[matched[ri]]
            binding[lang]["correct"]+=int(all(eq_field(k,r.get(k),h.get(k)) for k in CORE_FIELDS))
            for k in operator[lang]:
                if k=="negation":
                    ok=bool(r.get(k))==bool(h.get(k));pos=bool(r.get(k))
                else:
                    ok=eq_field(k,r.get(k),h.get(k));pos=r.get(k) not in (None,"")
                operator[lang][k]["correct"]+=int(ok);operator[lang][k]["total"]+=1
                if pos:
                    operator[lang][k]["positive_total"]+=1
                    operator[lang][k]["positive_correct"]+=int(ok)
        fer=fer_eval.evaluate({"financial_facts":refs,"language":lang,"text":s["text"]},s["text"])
        fer_by_lang[lang].append(fer["fer"])

    result={"overall":{k:_prf(v) for k,v in overall.items()},"by_language":{}}
    all_fer=[]
    for lang,c in langs.items():
        fs=fer_by_lang[lang];all_fer+=fs
        result["by_language"][lang]={
            **{k:_prf(v) for k,v in c.items()},
            "binding_accuracy":binding[lang]["correct"]/max(1,binding[lang]["total"]),
            "fer_floor_mean":sum(fs)/max(1,len(fs)),
            "operators":{
                k:{
                    "all_accuracy":v["correct"]/max(1,v["total"]),
                    "positive_accuracy":v["positive_correct"]/max(1,v["positive_total"]),
                    "positive_n":v["positive_total"]
                } for k,v in operator[lang].items()
            }
        }
    result["binding_accuracy"]=sum(v["correct"] for v in binding.values())/max(1,sum(v["total"] for v in binding.values()))
    result["fer_floor_mean"]=sum(all_fer)/max(1,len(all_fer))
    result["operators"]={}
    for k in ("negation","comparison","direction"):
        c=sum(operator[l][k]["correct"] for l in operator)
        t=sum(operator[l][k]["total"] for l in operator)
        pc=sum(operator[l][k]["positive_correct"] for l in operator)
        pt=sum(operator[l][k]["positive_total"] for l in operator)
        result["operators"][k]={"all_accuracy":c/max(1,t),"positive_accuracy":pc/max(1,pt),"positive_n":pt}
    return result
