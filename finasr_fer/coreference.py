PRONOUNS = {
    "en":["the company","the bank","the firm","the group","management","it"],
    "zh":["该公司","该行","该集团","其","管理层"],
    "ja":["同社","同行","当社","同グループ","経営陣"],
}
def resolve_coreference(text, language, entities):
    mentions=[]
    low=text.lower()
    for e in entities:
        start=0
        while True:
            p=low.find(e.lower(),start)
            if p<0: break
            mentions.append({"surface":text[p:p+len(e)],"canonical":e,"span":[p,p+len(e)],"explicit":True})
            start=p+len(e)
    mentions.sort(key=lambda x:x["span"][0])
    if not mentions:return mentions
    for pr in PRONOUNS.get(language,[]):
        start=0
        while True:
            p=low.find(pr.lower(),start)
            if p<0: break
            prev=[m for m in mentions if m["span"][1] <= p]
            if prev:
                ant=prev[-1]
                mentions.append({"surface":text[p:p+len(pr)],"canonical":ant["canonical"],"span":[p,p+len(pr)],"explicit":False})
            start=p+len(pr)
    return sorted(mentions,key=lambda x:x["span"][0])
