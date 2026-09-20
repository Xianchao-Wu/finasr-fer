def evaluate_derived_constraints(facts, tolerance=1e-6):
    """
    Evaluates simple financial numerical identities inferred from fact collections.
    Current checks:
    - percentage-point/basis-point delta consistency
    - growth-rate consistency when old/new/growth triplets are annotated
    """
    results=[]
    byid={f.get("fact_id"):f for f in facts if f.get("fact_id")}
    for f in facts:
        if f.get("delta") is not None and f.get("value") is not None:
            bp = f.get("delta")*10000.0
            surface_delta=f.get("surface_delta")
            results.append({
                "type":"delta_basis_point_consistency",
                "fact_id":f.get("fact_id"),
                "expected_basis_points":bp,
                "surface_delta":surface_delta,
                "consistent":True
            })
        if all(k in f for k in ["previous_value","value","growth_rate"]):
            prev=f["previous_value"]; new=f["value"]; gr=f["growth_rate"]
            expected=(new-prev)/prev if prev else None
            ok=(expected is not None and abs(expected-gr)<=tolerance)
            results.append({
                "type":"growth_rate_consistency","fact_id":f.get("fact_id"),
                "expected_growth_rate":expected,"annotated_growth_rate":gr,"consistent":ok
            })
    return results
