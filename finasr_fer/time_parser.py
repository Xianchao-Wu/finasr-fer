import re

ZH_Q={"一":"1","二":"2","三":"3","四":"4"}
EN_Q={"first":"1","second":"2","third":"3","fourth":"4"}

PATTERNS=[
    ("en_fyq",re.compile(r"\b(?:FY\s*)?(20\d{2})\s*Q([1-4])\b",re.I)),
    ("en_qfy",re.compile(r"\bQ([1-4])\s*(?:FY\s*)?(20\d{2})\b",re.I)),
    ("en_words",re.compile(r"\b(first|second|third|fourth) quarter of fiscal (20\d{2})\b",re.I)),
    ("en_full_year",re.compile(r"\bfull[- ]year\s+(20\d{2})\b",re.I)),
    ("en_fy",re.compile(r"\bFY\s*(20\d{2})\b",re.I)),
    ("en_fiscal_year",re.compile(r"\bfiscal(?: year)?\s+(20\d{2})\b",re.I)),
    ("zh_qnum",re.compile(r"(20\d{2})年(?:第)?([1-4])季度")),
    ("zh_qhan",re.compile(r"(20\d{2})年(?:第)?([一二三四])季度")),
    ("zh_fy",re.compile(r"(20\d{2})财年")),
    ("zh_year_fy",re.compile(r"(20\d{2})年度")),
    ("zh_year_full",re.compile(r"(20\d{2})年全年")),
    ("zh_h1",re.compile(r"(20\d{2})年上半年")),
    ("zh_h2",re.compile(r"(20\d{2})年下半年")),
    ("zh_9m",re.compile(r"(20\d{2})年前九个月")),
    ("ja_q",re.compile(r"(20\d{2})年3月期第([1-4])四半期")),
    ("ja_fyq",re.compile(r"(20\d{2})年度第([1-4])四半期")),
    ("ja_year_q",re.compile(r"(20\d{2})年第([1-4])四半期")),
    ("ja_fy",re.compile(r"(20\d{2})年3月期")),
    ("ja_year_fy",re.compile(r"(20\d{2})年度")),
]

RELATIVE={
    "en":{
        "this quarter":"REL_THIS_Q","current quarter":"REL_THIS_Q",
        "prior quarter":"REL_PREV_Q","prior-quarter":"REL_PREV_Q","previous quarter":"REL_PREV_Q","previous-quarter":"REL_PREV_Q","one quarter earlier":"REL_PREV_Q",
        "next quarter":"REL_NEXT_Q","next-quarter":"REL_NEXT_Q","following quarter":"REL_NEXT_Q",
        "same period last year":"REL_YOY_PERIOD","same quarter last year":"REL_YOY_PERIOD",
        "comparable quarter last year":"REL_YOY_PERIOD","a year earlier":"REL_YOY_PERIOD",
        "full year":"REL_FY","full-year":"REL_FY","second half":"REL_H2","first half":"REL_H1"
    },
    "zh":{
        "本季度":"REL_THIS_Q","本季":"REL_THIS_Q","同期":"REL_THIS_Q",
        "上季度":"REL_PREV_Q","上一季度":"REL_PREV_Q",
        "下一季度":"REL_NEXT_Q","下季度":"REL_NEXT_Q",
        "去年同期":"REL_YOY_PERIOD","上年同期":"REL_YOY_PERIOD",
        "全年":"REL_FY","下半年":"REL_H2","上半年":"REL_H1"
    },
    "ja":{
        "今四半期":"REL_THIS_Q","当四半期":"REL_THIS_Q","同期":"REL_THIS_Q",
        "前四半期":"REL_PREV_Q","次四半期":"REL_NEXT_Q",
        "前年同期":"REL_YOY_PERIOD","通期":"REL_FY","下期":"REL_H2","上期":"REL_H1"
    }
}

def extract_times(text,language="en"):
    out=[]
    for kind,pat in PATTERNS:
        for m in pat.finditer(text):
            if kind=="en_fyq":
                y,q=m.group(1),m.group(2);can=f"FY{y}Q{q}"
            elif kind=="en_qfy":
                q,y=m.group(1),m.group(2);can=f"FY{y}Q{q}"
            elif kind=="en_words":
                q=EN_Q[m.group(1).lower()];y=m.group(2);can=f"FY{y}Q{q}"
            elif kind in ("en_full_year","en_fy","en_fiscal_year"):
                can=f"FY{m.group(1)}"
            elif kind=="zh_qnum":
                y,q=m.group(1),m.group(2);can=f"FY{y}Q{q}"
            elif kind=="zh_qhan":
                y,q=m.group(1),ZH_Q[m.group(2)];can=f"FY{y}Q{q}"
            elif kind in ("zh_fy","zh_year_fy"):
                can=f"FY{m.group(1)}"
            elif kind=="zh_year_full":
                can=f"FY{m.group(1)}"
            elif kind=="zh_h1":
                can=f"FY{m.group(1)}H1"
            elif kind=="zh_h2":
                can=f"FY{m.group(1)}H2"
            elif kind=="zh_9m":
                can=f"FY{m.group(1)}9M"
            elif kind in ("ja_q","ja_fyq","ja_year_q"):
                can=f"FY{m.group(1)}Q{m.group(2)}"
            elif kind in ("ja_fy","ja_year_fy"):
                can=f"FY{m.group(1)}"
            out.append({"surface":m.group(0),"canonical":can,"span":[m.start(),m.end()]})

    for surf,can in RELATIVE.get(language,{}).items():
        start=0
        while True:
            p=text.find(surf,start)
            if p<0:break
            out.append({"surface":surf,"canonical":can,"span":[p,p+len(surf)]})
            start=p+len(surf)

    kept=[]
    for x in sorted(out,key=lambda z:(-(z["span"][1]-z["span"][0]),z["span"][0])):
        if any(not (x["span"][1]<=k["span"][0] or x["span"][0]>=k["span"][1]) for k in kept):
            continue
        kept.append(x)
    return sorted(kept,key=lambda z:z["span"][0])


def _parse_abs(can):
    m=re.fullmatch(r"FY?(\d{4})(?:Q([1-4]))?",can or "")
    if not m:return None
    return int(m.group(1)), int(m.group(2)) if m.group(2) else None

def _prev_quarter(y,q):
    if q>1:return y,q-1
    return y-1,4

def _next_quarter(y,q):
    if q<4:return y,q+1
    return y+1,1

def resolve_relative_times(times):
    """
    Resolve relative fiscal mentions against the nearest absolute anchor.
    Unlike v0.5, this works when a relative phrase precedes its anchor
    (e.g. "after a prior-quarter reading ..., FY2028 Q4 ...").
    """
    ordered=sorted(times,key=lambda x:x["span"][0])
    absolutes=[]
    for i,t in enumerate(ordered):
        av=_parse_abs(t.get("canonical"))
        if av:
            absolutes.append((i,t,av))

    out=[]
    for i,t in enumerate(ordered):
        can=t["canonical"]
        if _parse_abs(can):
            out.append(dict(t)); continue

        nt=dict(t)
        # Choose closest absolute mention by character distance.
        anchor=None
        if absolutes:
            center=(t["span"][0]+t["span"][1])/2
            _,at,av=min(
                absolutes,
                key=lambda z: abs(center-(z[1]["span"][0]+z[1]["span"][1])/2)
            )
            anchor=av

        if anchor:
            y,q=anchor
            if can=="REL_THIS_Q" and q:
                nt["canonical"]=f"FY{y}Q{q}"
            elif can=="REL_FY":
                nt["canonical"]=f"FY{y}"
            elif can=="REL_H1":
                nt["canonical"]=f"FY{y}H1"
            elif can=="REL_H2":
                nt["canonical"]=f"FY{y}H2"
            elif can=="REL_PREV_Q" and q:
                py,pq=_prev_quarter(y,q)
                nt["canonical"]=f"FY{py}Q{pq}"
            elif can=="REL_NEXT_Q" and q:
                ny,nq=_next_quarter(y,q)
                nt["canonical"]=f"FY{ny}Q{nq}"
            elif can=="REL_YOY_PERIOD" and q:
                nt["canonical"]=f"FY{y-1}Q{q}"
        out.append(nt)
    return sorted(out,key=lambda x:x["span"][0])
