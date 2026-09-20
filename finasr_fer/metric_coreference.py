import re

METRIC_PRONOUNS={
    "en":["the same metric","this metric","that metric","the ratio","the margin","it"],
    "zh":["这一指标","该指标","这个指标","同一指标","该比率","该利润率"],
    "ja":["同指標","この指標","同じ指標","当該指標","同比率"]
}

def resolve_metric_coreference(text,language,metric_mentions):
    out=list(metric_mentions)
    if not metric_mentions:return out
    low=text.lower()
    for pr in METRIC_PRONOUNS.get(language,[]):
        start=0
        while True:
            p=low.find(pr.lower(),start)
            if p<0:break
            prev=[m for m in out if m["span"][1] <= p]
            # Favor prior explicit metric mention.
            if prev:
                ant=sorted(prev,key=lambda x:x["span"][1])[-1]
                out.append({"surface":text[p:p+len(pr)],"canonical":ant["canonical"],
                            "span":[p,p+len(pr)],"explicit":False})
            start=p+len(pr)
    return sorted(out,key=lambda x:x["span"][0])
