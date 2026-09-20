from .metrics import word_error_rate,char_error_rate
from .normalization import normalize_text,value_distance
from .parser import FinancialFactExtractor
from .alignment import align_facts
from .consistency import evaluate_derived_constraints

DEFAULT_WEIGHTS={
    "entity":1.0,"metric":1.0,"value":2.5,"unit":1.5,"currency":1.5,"binding":2.5,
    "negation":2.5,"comparison":2.5,"direction":2.0,"time":1.5,
    "term":1.0,"ticker":1.0,"acronym":1.0
}

class StructuredFEREvaluator:
    def __init__(self,weights=None,value_tau=2.302585092994046,extractor=None,alignment_weights=None,
                 mode="auto",spurious_fact_weight=2.5):
        self.weights=dict(DEFAULT_WEIGHTS)
        if weights:self.weights.update(weights)
        self.value_tau=value_tau
        self.extractor=extractor or FinancialFactExtractor()
        self.alignment_weights=alignment_weights
        self.mode=mode
        self.spurious_fact_weight=float(spurious_fact_weight)

    def _eq(self,a,b):
        if a is None or b is None:return a is b
        return normalize_text(str(a))==normalize_text(str(b))

    def _fact_errors(self,r,h):
        e={}
        e["entity"]=0 if self._eq(r.get("entity"),h.get("entity")) else (1 if r.get("entity") is not None else 0)
        e["metric"]=0 if self._eq(r.get("metric"),h.get("metric")) else (1 if r.get("metric") is not None else 0)
        e["value"]=value_distance(r.get("value"),h.get("value"),self.value_tau) if r.get("value") is not None else 0
        for k in ["unit","currency","negation","comparison","direction","time","term","ticker","acronym"]:
            e[k]=0 if r.get(k) is None else (0 if self._eq(r.get(k),h.get(k)) else 1)
        comps=[]
        if r.get("entity") is not None:comps.append(e["entity"])
        if r.get("metric") is not None:comps.append(e["metric"])
        if r.get("value") is not None:comps.append(1 if e["value"]>1e-9 else 0)
        e["binding"]=1 if len(comps)>=2 and any(x>0 for x in comps) else 0
        return e

    def critical_token_accuracy(self,tokens,h):
        nh=normalize_text(h)
        ok=[t for t in tokens if normalize_text(t) in nh]
        miss=[t for t in tokens if normalize_text(t) not in nh]
        return {"critical_token_accuracy":len(ok)/max(1,len(tokens)) if tokens else 1.0,
                "critical_token_total":len(tokens),"critical_token_correct":len(ok),"missed_critical_tokens":miss}

    def evaluate(self,reference,hypothesis_text,hypothesis_facts=None,mode=None):
        mode=mode or self.mode
        rt=reference.get("text") or reference.get("reference_text") or ""
        lang=reference.get("language","en")
        wer=word_error_rate(normalize_text(rt),normalize_text(hypothesis_text))
        cer=char_error_rate(normalize_text(rt).replace(" ",""),normalize_text(hypothesis_text).replace(" ",""))
        crit=self.critical_token_accuracy(reference.get("critical_tokens",[]),hypothesis_text)
        rf=reference.get("financial_facts",[])

        if mode=="struct":
            if hypothesis_facts is None:
                raise ValueError("mode='struct' requires explicit hypothesis_facts")
            hf=hypothesis_facts
        else:
            hf=hypothesis_facts if hypothesis_facts is not None else self.extractor.extract(hypothesis_text,lang)

        ali=align_facts(rf,hf,weights=self.alignment_weights)
        num={k:0.0 for k in self.weights}; den={k:0.0 for k in self.weights}; fr=[]

        # FER v0.7: explicitly bounded fact-level corruption.
        # For each reference fact i, D_i is its active financial-information mass.
        # A matched fact contributes min(L_ij, D_i) = D_i * min(1, L_ij / D_i).
        # Hence each reference fact contributes at most its own denominator mass,
        # which makes the corpus/utterance FER provably bounded in [0, 1].
        matched_bounded_num=0.0
        reference_mass=0.0

        for p in ali["pairs"]:
            r=rf[p["ref_index"]]; h=hf[p["hyp_index"]]
            errs=self._fact_errors(r,h)
            raw_fact_loss=0.0
            active_mass=0.0
            for k,w in self.weights.items():
                exists=(k=="binding") or (r.get(k) is not None)
                if exists:
                    # Component errors are intended to be normalized to [0,1].
                    # Clamp defensively so a custom extractor/scorer cannot break
                    # the FER range guarantee.
                    ek=min(1.0,max(0.0,float(errs[k])))
                    errs[k]=ek
                    num[k]+=w*ek
                    den[k]+=w
                    raw_fact_loss+=w*ek
                    active_mass+=w

            normalized_fact_loss=(raw_fact_loss/active_mass) if active_mass else 0.0
            normalized_fact_loss=min(1.0,max(0.0,normalized_fact_loss))
            bounded_fact_loss=active_mass*normalized_fact_loss
            matched_bounded_num+=bounded_fact_loss
            reference_mass+=active_mass

            fr.append({
                "fact_id":r.get("fact_id"),
                "matched_hyp_index":p["hyp_index"],
                "alignment_cost":p["cost"],
                "errors":errs,
                "raw_fact_loss":raw_fact_loss,
                "active_weight_mass":active_mass,
                "normalized_fact_loss":normalized_fact_loss,
                "bounded_fact_loss":bounded_fact_loss
            })

        missing_num=0.0
        for i in ali["unmatched_ref"]:
            r=rf[i]; errs={k:1.0 for k in self.weights}
            active_mass=0.0
            for k,w in self.weights.items():
                exists=(k=="binding") or (r.get(k) is not None)
                if exists:
                    num[k]+=w;den[k]+=w
                    active_mass+=w
            missing_num+=active_mass
            reference_mass+=active_mass
            fr.append({
                "fact_id":r.get("fact_id"),
                "matched_hyp_index":None,
                "alignment_cost":1.0,
                "errors":errs,
                "raw_fact_loss":active_mass,
                "active_weight_mass":active_mass,
                "normalized_fact_loss":1.0 if active_mass else 0.0,
                "bounded_fact_loss":active_mass
            })

        # Each unmatched hypothesis fact is a fully erroneous structural slot.
        # Adding the same mass to numerator and denominator preserves the [0,1] bound
        # while making FER approach 1 as hallucinated financial facts accumulate.
        spur_num=self.spurious_fact_weight*len(ali["unmatched_hyp"])
        spur_den=spur_num
        total_num=matched_bounded_num+missing_num+spur_num
        total_den=reference_mass+spur_den
        fer=total_num/total_den if total_den else 0.0
        # Numerical safeguard only; boundedness follows from the fact-level definition.
        fer=min(1.0,max(0.0,fer))
        comp={}
        for k in self.weights:
            comp[f"{k}_error"]=num[k]/den[k] if den[k] else None
            comp[f"{k}_accuracy"]=1-comp[f"{k}_error"] if den[k] else None

        return {
            "id":reference.get("id"),"language":lang,"category":reference.get("category"),
            "mode":mode,"wer":wer["wer"],"cer":cer["cer"],**crit,"fer":fer,
            "alignment_cost":ali["cost"],"num_reference_facts":len(rf),"num_hypothesis_facts":len(hf),
            "unmatched_reference_facts":len(ali["unmatched_ref"]),"unmatched_hypothesis_facts":len(ali["unmatched_hyp"]),
            "spurious_fact_error":len(ali["unmatched_hyp"])/max(1,len(rf)+len(ali["unmatched_hyp"])),
            "spurious_fact_weight":self.spurious_fact_weight,
            "bounded_numerator":total_num,"total_information_mass":total_den,
            **comp,"fact_results":fr,"alignment":ali,"hypothesis_facts":hf,
            "derived_consistency":evaluate_derived_constraints(hf)
        }

def evaluate_pair(reference,hypothesis_text,weights=None):
    return StructuredFEREvaluator(weights=weights).evaluate(reference,hypothesis_text)

def aggregate_fer(rows):
    """Aggregate FER by information mass (micro/corpus FER), not by utterance mean.

    This is the preferred dataset-level FER for v0.7+: sum_i N_i / sum_i D_i.
    Macro FER is returned separately for diagnostics.
    """
    valid=[r for r in rows if r is not None and r.get("fer") is not None]
    if not valid:
        return {"fer":None,"fer_macro":None,"bounded_numerator":0.0,
                "total_information_mass":0.0,"num_samples":0}
    num=sum(float(r.get("bounded_numerator",0.0)) for r in valid)
    den=sum(float(r.get("total_information_mass",0.0)) for r in valid)
    fer=num/den if den>0 else 0.0
    fer=min(1.0,max(0.0,fer))
    return {"fer":fer,"fer_macro":sum(float(r["fer"]) for r in valid)/len(valid),
            "bounded_numerator":num,"total_information_mass":den,"num_samples":len(valid)}


def evaluate_dataset(references,hypotheses,weights=None):
    ev=StructuredFEREvaluator(weights=weights)
    rows=[ev.evaluate(r,hypotheses[r["id"]]) for r in references if r.get("id") in hypotheses]
    if not rows:return {"num_samples":0,"samples":[]}
    keys=["wer","cer","critical_token_accuracy","fer","alignment_cost","entity_error","metric_error",
          "value_error","unit_error","currency_error","binding_error","negation_error",
          "comparison_error","direction_error","time_error"]
    out={"num_samples":len(rows)}
    for k in keys:
        vals=[x[k] for x in rows if x.get(k) is not None]
        out[k]=sum(vals)/len(vals) if vals else None
    agg=aggregate_fer(rows)
    out["fer_macro"]=out.get("fer")
    out["fer"]=agg["fer"]
    out["bounded_numerator"]=agg["bounded_numerator"]
    out["total_information_mass"]=agg["total_information_mass"]
    out["samples"]=rows
    return out
