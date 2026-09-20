import re
from typing import List, Dict

# Sentence separators, but decimal points such as 2.50 must not split a scope.
SENT_SPLIT = re.compile(r"[。！？；;!?]+|\.(?!\d)")
MAJOR_CONNECTORS = re.compile(r"\bwhile\b|\bwhereas\b|\bbut\b|另一方面|而另一方面|一方で|しかし", re.I)

NEG_PATTERNS = [
    r"\bnot\b", r"\bdoes not\b", r"\bdo not\b", r"\bdid not\b", r"\bcannot\b", r"\bcan't\b",
    r"\bwon't\b", r"\bwould not\b", r"\bno longer\b",
    r"并不", r"不会", r"不能", r"没有", r"未", r"不再", r"并非", r"不预计", r"不认为",
    r"ない", r"ません", r"ではない", r"しない", r"見込んでいません", r"わけではない"
]
CMP_PATTERNS = {
    "greater_than":[r"\babove\b",r"\bover\b",r"\bexceed(?:s|ed|ing)?\b",r"\bmore than\b",
                    r"\bgreater than\b",r"高于",r"超过",r"大于",r"上回る",r"超える",r"超"],
    "less_than":[r"\bbelow\b",r"\bunder\b",r"\bless than\b",r"\blower than\b",
                 r"低于",r"小于",r"跌破",r"下回る",r"未満"],
    "at_least":[r"\bat least\b",r"\bno lower than\b",r"\bnot less than\b",
                r"至少",r"不低于",r"下限为",r"以上",r"少なくとも"],
    "at_most":[r"\bat most\b",r"\bno more than\b",r"\bnot above\b",
               r"不超过",r"不会高于",r"至多",r"上限为",r"以下"],
}
DIR_PATTERNS = {
    "increase":[r"\bincrease",r"\bimprov",r"\brise",r"\brose\b",r"\bup\b",r"\bwiden",r"\bhigher\b",
                r"提高",r"增长",r"上升",r"扩大",r"抬升",r"改善",r"増加",r"上昇",r"拡大",r"改善"],
    "decrease":[r"\bdecrease",r"\bdeclin",r"\bfall",r"\bfell\b",r"\bdown\b",r"\bnarrow",r"\blower\b",
                r"下降",r"降低",r"减少",r"收窄",r"跌",r"恶化",r"減少",r"低下",r"縮小",r"悪化"],
}

def split_scopes(text: str) -> List[Dict]:
    spans=[]; start=0
    for m in SENT_SPLIT.finditer(text):
        end=m.start()
        if end>start:
            segment=text[start:end]
            sub_start=start
            for cm in MAJOR_CONNECTORS.finditer(segment):
                ce=start+cm.start()
                if ce>sub_start:
                    spans.append({"text":text[sub_start:ce].strip(),"span":[sub_start,ce]})
                sub_start=start+cm.end()
            if sub_start<end:
                spans.append({"text":text[sub_start:end].strip(),"span":[sub_start,end]})
        start=m.end()
    if start<len(text):
        spans.append({"text":text[start:].strip(),"span":[start,len(text)]})
    return [x for x in spans if x["text"]]

def clause_for_span(text: str, span) -> Dict:
    mid=(span[0]+span[1])/2
    for c in split_scopes(text):
        if c["span"][0] <= mid <= c["span"][1]:
            return c
    s=max(0,span[0]-160);e=min(len(text),span[1]+160)
    return {"text":text[s:e],"span":[s,e]}

def detect_negation(text: str) -> bool:
    return any(re.search(p,text,re.I) for p in NEG_PATTERNS)

def detect_comparison(text: str):
    for label in ["at_least","at_most","greater_than","less_than"]:
        if any(re.search(p,text,re.I) for p in CMP_PATTERNS[label]):
            return label
    return None

def detect_direction(text: str):
    labs=[]
    for label,pats in DIR_PATTERNS.items():
        if any(re.search(p,text,re.I) for p in pats):
            labs.append(label)
    return labs[0] if len(labs)==1 else None
