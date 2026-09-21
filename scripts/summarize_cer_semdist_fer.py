#!/usr/bin/env python3
import argparse, json, re, unicodedata
from pathlib import Path

def norm_cjk(s):
    s=unicodedata.normalize("NFKC", str(s)).lower()
    s=re.sub(r"\s+","",s)
    s=re.sub(r"[^\w\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\u31f0-\u31ff]","",s)
    return s

def ed(a,b):
    prev=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        cur=[i]
        for j,y in enumerate(b,1):
            cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(x!=y)))
        prev=cur
    return prev[-1]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("jsonl")
    args=ap.parse_args()
    rows=[json.loads(x) for x in Path(args.jsonl).read_text(encoding="utf-8").splitlines() if x.strip()]
    S=N=0; sem=[]; fer=[]
    for r in rows:
        ref=norm_cjk(r.get("reference",r.get("text","")))
        hyp=norm_cjk(r.get("hypothesis",""))
        S += ed(ref,hyp); N += len(ref)
        if r.get("semdist") is not None: sem.append(float(r["semdist"]))
        if r.get("fer_version")=="0.8" and r.get("fer") is not None: fer.append(float(r["fer"]))
    print("N",len(rows))
    print("CER",S/N if N else float("nan"))
    print("CER_pct",100*S/N if N else float("nan"))
    print("SemDist",sum(sem)/len(sem) if sem else float("nan"))
    print("FER_v08",sum(fer)/len(fer) if fer else "not_computed")
if __name__=="__main__": main()
