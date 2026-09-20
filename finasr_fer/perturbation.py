from collections import defaultdict
from .evaluator import StructuredFEREvaluator

def evaluate_perturbation_set(items,evaluator=None):
    ev=evaluator or StructuredFEREvaluator()
    rows=[];bt=defaultdict(list)
    for item in items:
        ref={"id":item.get("source_id") or item.get("id"),"language":item.get("language"),
             "category":item.get("category"),"text":item.get("reference_text"),
             "critical_tokens":item.get("critical_tokens",[]),
             "financial_facts":item.get("financial_facts",[])}
        base=ev.evaluate(ref,ref["text"])
        for p in item.get("perturbations",[]):
            r=ev.evaluate(ref,p["hypothesis_text"])
            rec={"id":item.get("id"),"source_id":item.get("source_id"),
                 "language":item.get("language"),"variant_id":p.get("variant_id"),
                 "error_type":p.get("error_type"),"wer":r["wer"],"cer":r["cer"],"fer":r["fer"],
                 "delta_fer":r["fer"]-base["fer"],"critical_token_accuracy":r["critical_token_accuracy"],
                 "binding_error":r.get("binding_error"),"value_error":r.get("value_error"),
                 "negation_error":r.get("negation_error"),"comparison_error":r.get("comparison_error"),
                 "direction_error":r.get("direction_error"),"time_error":r.get("time_error")}
            rows.append(rec);bt[rec["error_type"]].append(rec)
    summ={}
    for t,rs in bt.items():
        def mean(k):
            vals=[x[k] for x in rs if x.get(k) is not None]
            return sum(vals)/len(vals) if vals else None
        summ[t]={"n":len(rs),"wer":mean("wer"),"cer":mean("cer"),"fer":mean("fer"),
                 "delta_fer":mean("delta_fer"),"critical_token_accuracy":mean("critical_token_accuracy"),
                 "binding_error":mean("binding_error"),"value_error":mean("value_error"),
                 "negation_error":mean("negation_error"),"comparison_error":mean("comparison_error"),
                 "direction_error":mean("direction_error"),"time_error":mean("time_error")}
    return {"num_variants":len(rows),"by_error_type":summ,"variants":rows}
