import json
def read_jsonl(path):
    out=[]
    with open(path,encoding="utf-8") as f:
        for line in f:
            if line.strip():out.append(json.loads(line))
    return out
def read_hypotheses_jsonl(path,id_field="id",text_field="hypothesis_text"):
    out={}
    with open(path,encoding="utf-8") as f:
        for line in f:
            if line.strip():
                x=json.loads(line);out[x[id_field]]=x[text_field]
    return out
