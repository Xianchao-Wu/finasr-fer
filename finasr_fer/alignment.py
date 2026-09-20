from .normalization import value_distance, normalized_string_similarity

def fact_cost(ref,hyp,weights=None):
    w={"entity":1.5,"metric":1.5,"value":2.5,"unit":1.0,"currency":1.0,"time":1.0,
       "ticker":1.0,"term":0.8,"acronym":0.8}
    if weights:w.update(weights)
    num=den=0.0
    for k in ["entity","metric","unit","currency","time","ticker","term","acronym"]:
        if ref.get(k) is not None:
            den+=w[k]
            if k in ["entity","metric","term"]:
                num+=w[k]*(1-normalized_string_similarity(ref.get(k),hyp.get(k)))
            else:
                num+=w[k]*(0.0 if ref.get(k)==hyp.get(k) else 1.0)
    if ref.get("value") is not None:
        den+=w["value"]
        num+=w["value"]*value_distance(ref.get("value"),hyp.get("value"))
    return num/den if den else 0.0

def _assignment(cost):
    try:
        import numpy as np
        from scipy.optimize import linear_sum_assignment
        r,c=linear_sum_assignment(np.asarray(cost,float))
        return list(zip(r.tolist(),c.tolist()))
    except Exception:
        flat=[]; ur=set(); uc=set(); out=[]
        for i,row in enumerate(cost):
            for j,v in enumerate(row): flat.append((v,i,j))
        for v,i,j in sorted(flat):
            if i not in ur and j not in uc:
                out.append((i,j)); ur.add(i); uc.add(j)
        return out

def align_facts(ref_facts,hyp_facts,unmatched_cost=1.0,weights=None):
    n,m=len(ref_facts),len(hyp_facts)
    if n==0:return {"pairs":[],"unmatched_ref":[],"unmatched_hyp":list(range(m)),"cost":0.0}
    if m==0:return {"pairs":[],"unmatched_ref":list(range(n)),"unmatched_hyp":[],"cost":1.0}
    size=max(n,m)
    mat=[[unmatched_cost]*size for _ in range(size)]
    for i in range(n):
        for j in range(m):
            mat[i][j]=fact_cost(ref_facts[i],hyp_facts[j],weights)
    pairs=[]; mr=set(); mh=set(); total=0.0
    for i,j in _assignment(mat):
        if i<n and j<m:
            pairs.append({"ref_index":i,"hyp_index":j,"cost":mat[i][j]})
            mr.add(i); mh.add(j); total+=mat[i][j]
    ur=[i for i in range(n) if i not in mr]
    uh=[j for j in range(m) if j not in mh]
    total+=unmatched_cost*len(ur)
    return {"pairs":pairs,"unmatched_ref":ur,"unmatched_hyp":uh,"cost":total/max(1,n)}
