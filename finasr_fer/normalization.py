import re, math, unicodedata

WS=re.compile(r"\s+")
PUNCT=re.compile(r"[，。！？；：、,.!?;:\"'“”‘’（）()\[\]{}]")
NUM_RE=r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?"

def normalize_text(text,lowercase=True,remove_punctuation=True):
    text=unicodedata.normalize("NFKC",text or "")
    if lowercase:text=text.lower()
    if remove_punctuation:text=PUNCT.sub(" ",text)
    return WS.sub(" ",text).strip()

def _first_num(s):
    m=re.search(NUM_RE,s)
    return float(m.group(0).replace(",","")) if m else None

def parse_financial_quantity(surface,language=None):
    if not surface:return None
    s=unicodedata.normalize("NFKC",str(surface)).strip()
    low=s.lower()
    x=_first_num(s)
    if x is None:return None
    out={"surface":surface,"raw_number":x,"value":x,"unit":"number","currency":None,"scale":1.0}

    # Currency first. Full-width yen is normalized by NFKC.
    if "$" in s or "usd" in low or "美元" in s or "美金" in s or "ドル" in s or "米ドル" in s:
        out["currency"]="USD"
    elif "¥" in s or "jpy" in low or "円" in s:
        out["currency"]="JPY"
    elif "人民币" in s or "rmb" in low or "cny" in low or ("元" in s and "美元" not in s):
        out["currency"]="CNY"
    elif "eur" in low or "€" in s or "欧元" in s or "ユーロ" in s:
        out["currency"]="EUR"
    elif "gbp" in low or "£" in s or "英镑" in s or "ポンド" in s:
        out["currency"]="GBP"

    # Ratios / deltas. Currency must be cleared for ratio expressions.
    if ("basis point" in low or re.search(r"\bbps?\b",low) or
        "ベーシスポイント" in s or "bp" == low.strip() or
        "个基点" in s or "個基点" in s or "基点" in s):
        out.update({"value":x/10000.0,"unit":"delta","scale":0.0001,"currency":None})
        return out
    if ("percentage point" in low or "个百分点" in s or "パーセントポイント" in s):
        out.update({"value":x/100.0,"unit":"delta","scale":0.01,"currency":None})
        return out
    if "%" in s or "percent" in low or "パーセント" in s or "百分比" in s:
        out.update({"value":x/100.0,"unit":"ratio","scale":0.01,"currency":None})
        return out

    # Ordered longest/specific units first.
    scale=1.0
    if "quadrillion" in low:scale=1e15
    elif "trillion" in low:scale=1e12
    elif "billion" in low:scale=1e9
    elif "million" in low:scale=1e6
    elif "thousand" in low:scale=1e3
    # Japanese / Chinese East-Asian units.
    elif re.search(r"兆",s):scale=1e12
    elif re.search(r"千億|千亿",s):scale=1e11
    elif re.search(r"百億|百亿",s):scale=1e10
    elif re.search(r"十億|十亿",s):scale=1e9
    elif re.search(r"[億亿]",s):scale=1e8
    elif re.search(r"千万",s):scale=1e7
    elif re.search(r"百万",s):scale=1e6
    elif re.search(r"十万",s):scale=1e5
    elif "万" in s:scale=1e4

    out["scale"]=scale
    out["value"]=x*scale
    out["unit"]="absolute_money" if out["currency"] else ("scaled_number" if scale!=1 else "number")
    return out

def normalize_number_surface(surface):
    q=parse_financial_quantity(surface)
    return None if q is None else q["value"]

def canonicalize_money(surface):
    q=parse_financial_quantity(surface)
    return None if q is None else (q["currency"],q["value"])

def value_distance(v_ref,v_hyp,tau=math.log(10.0),eps=1e-12):
    if v_ref is None or v_hyp is None:return 1.0
    try:a=float(v_ref);b=float(v_hyp)
    except Exception:return 1.0
    if abs(a-b)<=eps:return 0.0
    if a*b<0:return 1.0
    if abs(a)<=eps or abs(b)<=eps:return min(1.0,abs(a-b)/(abs(a)+eps))
    return min(1.0,abs(math.log(abs(a)+eps)-math.log(abs(b)+eps))/tau)

def normalized_string_similarity(a,b):
    a=normalize_text(str(a or ""));b=normalize_text(str(b or ""))
    if not a and not b:return 1.0
    if not a or not b:return 0.0
    if a==b:return 1.0
    A={a[i:i+2] for i in range(max(1,len(a)-1))}
    B={b[i:i+2] for i in range(max(1,len(b)-1))}
    return 2*len(A&B)/max(1,len(A)+len(B))
