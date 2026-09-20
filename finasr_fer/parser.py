import re
from dataclasses import dataclass, field
from .normalization import parse_financial_quantity, normalize_text
from .ontology import DEFAULT_ENTITIES, DEFAULT_METRICS, METRIC_ALIASES, DEFAULT_TERMS, DEFAULT_TICKERS, DEFAULT_ACRONYMS
from .clause import clause_for_span, detect_negation, detect_comparison, detect_direction
from .coreference import resolve_coreference
from .time_parser import extract_times, resolve_relative_times
from .metric_coreference import resolve_metric_coreference

QWORD = (
    r"(?:[$¥￥€£]\s*)?[-+]?\d+(?:,\d{3})*(?:\.\d+)?\s*(?:"
    r"quadrillion|trillion|billion|million|thousand|basis points?|bps?|bp|percentage points?|percent|%|"
    r"兆(?:円|元|ドル|ユーロ|ポンド)?|千[億亿](?:円|元|ドル|美元|ユーロ)?|百[億亿](?:円|元|ドル|美元|ユーロ)?|"
    r"十[億亿](?:円|元|ドル|美元|ユーロ)?|[亿億](?:円|元|ドル|美元|美金|ユーロ|ポンド)?|"
    r"千万(?:円|元|ドル)?|百万(?:円|元|ドル)?|十万(?:円|元|ドル)?|万(?:円|元|ドル|ユーロ|ポンド)?|"
    r"ベーシスポイント|パーセントポイント|パーセント|个百分点|个基点|個基点|基点|"
    r"亿元|億円|万元|万円)?"
)
QPAT=re.compile(QWORD,re.I)

@dataclass
class FinancialOntology:
    entities: dict = field(default_factory=lambda:{k:list(v) for k,v in DEFAULT_ENTITIES.items()})
    metrics: dict = field(default_factory=lambda:{k:list(v) for k,v in DEFAULT_METRICS.items()})
    metric_aliases: dict = field(default_factory=lambda:{k:dict(v) for k,v in METRIC_ALIASES.items()})
    terms: dict = field(default_factory=lambda:{k:list(v) for k,v in DEFAULT_TERMS.items()})
    tickers: list = field(default_factory=lambda:list(DEFAULT_TICKERS))
    acronyms: list = field(default_factory=lambda:list(DEFAULT_ACRONYMS))
    def add_entity(self,language,name): self.entities.setdefault(language,[]).append(name)
    def add_metric(self,language,name): self.metrics.setdefault(language,[]).append(name)
    def add_term(self,language,name): self.terms.setdefault(language,[]).append(name)
    def add_ticker(self,ticker): self.tickers.append(ticker)
    def add_acronym(self,acronym): self.acronyms.append(acronym)

class FinancialFactExtractor:
    def __init__(self,ontology=None,window_chars=120,max_binding_distance=220):
        self.ontology=ontology or FinancialOntology()
        self.window_chars=window_chars
        self.max_binding_distance=max_binding_distance

    @staticmethod
    def _find_terms(text,terms,word_boundary=False):
        candidates=[]
        for term in sorted(set(terms),key=len,reverse=True):
            if not term: continue
            if word_boundary and re.fullmatch(r"[A-Za-z0-9.]+",term):
                pat=re.compile(r"(?<![A-Za-z0-9])"+re.escape(term)+r"(?![A-Za-z0-9])",re.I)
            else:
                pat=re.compile(re.escape(term),re.I)
            for m in pat.finditer(text):
                candidates.append({"surface":m.group(0),"canonical":term,"span":[m.start(),m.end()]})
        candidates.sort(key=lambda z:(-(z["span"][1]-z["span"][0]),z["span"][0]))
        kept=[]
        for c in candidates:
            cs,ce=c["span"]
            if any(not (ce<=k["span"][0] or cs>=k["span"][1]) for k in kept):
                continue
            kept.append(c)
        return sorted(kept,key=lambda z:z["span"][0])

    def extract_entities(self,text,language):
        explicit=self._find_terms(text,self.ontology.entities.get(language,[])+self.ontology.entities.get("en",[]))
        names=[x["canonical"] for x in explicit]
        return resolve_coreference(text,language,names)

    def extract_metrics(self,text,language):
        base=self._find_terms(text,self.ontology.metrics.get(language,[])+self.ontology.metrics.get("en",[]),True)
        aliases=self.ontology.metric_aliases.get(language,{})
        alias_mentions=self._find_terms(text,list(aliases.keys()),True)
        for m in alias_mentions:
            m["canonical"]=aliases.get(m["canonical"],m["canonical"])
        candidates=base+alias_mentions
        candidates.sort(key=lambda z:(-(z["span"][1]-z["span"][0]),z["span"][0]))
        kept=[]
        for c in candidates:
            if any(not (c["span"][1]<=k["span"][0] or c["span"][0]>=k["span"][1]) for k in kept):
                continue
            c["explicit"]=True
            kept.append(c)
        kept=sorted(kept,key=lambda z:z["span"][0])
        return resolve_metric_coreference(text,language,kept)
    def extract_terms(self,text,language):
        return self._find_terms(text,self.ontology.terms.get(language,[])+self.ontology.terms.get("en",[]),True)
    def extract_tickers(self,text):
        return self._find_terms(text,self.ontology.tickers,True)
    def extract_acronyms(self,text):
        return self._find_terms(text,self.ontology.acronyms,True)
    def extract_times(self,text,language=None):
        return resolve_relative_times(extract_times(text,language))

    def extract_quantities(self,text,language=None):
        time_spans=[x["span"] for x in self.extract_times(text,language)]
        out=[]
        for m in QPAT.finditer(text):
            span=[m.start(),m.end()]
            if any(not (span[1] <= ts[0] or span[0] >= ts[1]) for ts in time_spans):
                continue
            s=m.group(0).strip()
            if not s: continue
            q=parse_financial_quantity(s,language)
            if q:
                q["span"]=span; out.append(q)
        return out

    @staticmethod
    def _distance(a,b):
        return abs((a[0]+a[1])/2-(b[0]+b[1])/2)

    def _nearest(self,target,cands,prefer_before=True):
        if not cands:return None
        before=[x for x in cands if x["span"][1]<=target[0]]
        after=[x for x in cands if x["span"][0]>=target[1]]
        pool=before if (prefer_before and before) else (after if after else cands)
        best=min(pool,key=lambda x:self._distance(target,x["span"]))
        return best if self._distance(target,best["span"])<=self.max_binding_distance else None

    def _same_clause_candidates(self,text,target,cands):
        c=clause_for_span(text,target)
        return [x for x in cands if x["span"][0]>=c["span"][0] and x["span"][1]<=c["span"][1]]


    def _sequence_metric_overrides(self,text,quantities,metrics):
        overrides={}
        cues=["respectively","分别","それぞれ"]
        scopes={}
        for q in quantities:
            c=clause_for_span(text,q["span"])
            scopes.setdefault(tuple(c["span"]),[]).append(q)
        for span,qs in scopes.items():
            s,e=span
            st=text[s:e]
            if not any(cue.lower() in st.lower() for cue in cues):
                continue
            ms=[x for x in metrics if x["span"][0]>=s and x["span"][1]<=e and x.get("explicit",True)]
            ordered=[]
            for x in sorted(ms,key=lambda z:z["span"][0]):
                if not any(y["span"]==x["span"] for y in ordered):
                    ordered.append(x)
            qsorted=sorted(qs,key=lambda z:z["span"][0])
            if len(ordered)>=2 and len(ordered)==len(qsorted):
                for m,q in zip(ordered,qsorted):
                    overrides[q["span"][0]]=m["canonical"]
        return overrides

    def _sequence_entity_overrides(self,text,quantities,entities):
        """
        Detect enumerations such as:
        A, B and C reported X, Y and Z, respectively.
        A、B、C披露的...分别为X、Y、Z。
        A、B、Cの...はそれぞれX、Y、Z。
        Returns {quantity_start: canonical_entity}.
        """
        overrides={}
        cues=["respectively","分别","それぞれ"]
        scopes={}
        for q in quantities:
            c=clause_for_span(text,q["span"])
            scopes.setdefault(tuple(c["span"]),[]).append(q)
        for span,qs in scopes.items():
            s,e=span
            scope_text=text[s:e]
            if not any(cue.lower() in scope_text.lower() for cue in cues):
                continue
            es=[x for x in entities if x["span"][0]>=s and x["span"][1]<=e and x.get("explicit",True)]
            # unique explicit entity mentions in textual order
            seen=set(); ordered=[]
            for x in sorted(es,key=lambda z:z["span"][0]):
                key=(x["span"][0],x["canonical"])
                if key not in seen:
                    ordered.append(x);seen.add(key)
            # Prefer a run of same-unit quantities matching entity count.
            qsorted=sorted(qs,key=lambda z:z["span"][0])
            for i in range(len(qsorted)):
                run=qsorted[i:i+len(ordered)]
                if len(ordered)>=2 and len(run)==len(ordered):
                    units=[x.get("unit") for x in run]
                    if len(set(units))==1:
                        for ent,qv in zip(ordered,run):
                            overrides[qv["span"][0]]=ent["canonical"]
                        break
        return overrides


    @staticmethod
    def _local_text(text,span,left=70,right=70):
        return text[max(0,span[0]-left):min(len(text),span[1]+right)]

    @staticmethod
    def _is_delta_context(text,language):
        low=text.lower()
        cues={
          "en":["basis point","bps","percentage point","change","increase","decrease","widen","narrow"],
          "zh":["基点","百分点","变化","上升","下降","扩大","收窄"],
          "ja":["ベーシスポイント","パーセントポイント","変化","上昇","低下","拡大","縮小"]
        }
        return any(x.lower() in low for x in cues.get(language,[]))

    @staticmethod
    def _is_growth_context(text,language):
        low=text.lower()
        cues={
          "en":["year-over-year growth","year over year growth","yoy growth","growth of","up "],
          "zh":["同比增长","同比上升","增长"],
          "ja":["前年同期比","増加率","成長率"]
        }
        return any(x.lower() in low for x in cues.get(language,[]))

    def _specialized_metric(self,base_metric,q,text,language):
        if not base_metric:
            return base_metric
        local=self._local_text(text,q["span"])
        # Explicit delta quantities represent change of the base financial metric.
        if q.get("unit")=="delta" and self._is_delta_context(local,language):
            return f"{base_metric} change"
        # A percentage explicitly described as YoY growth is a growth fact.
        if q.get("unit")=="ratio" and self._is_growth_context(local,language):
            return f"{base_metric} growth"
        return base_metric

    def _local_operator(self,text,span,kind,q=None,language="en"):
        before=text[max(0,span[0]-55):span[0]]
        after=text[span[1]:min(len(text),span[1]+70)]
        around=before+text[span[0]:span[1]]+after
        if kind=="negation":
            return detect_negation(around)

        if kind=="comparison":
            # Threshold operators may be prefix (above 5%) or postfix in CJK
            # (5%以上, 5%を下回る). Keep the literal predicate separate from negation.
            hist_cues=[
                "basis points above","basis points below","bps above","bps below",
                "percentage points above","percentage points below",
                "个基点高","个基点低","个百分点高","个百分点低",
                "ベーシスポイント上","ベーシスポイント下",
                "パーセントポイント上","パーセントポイント下"
            ]
            b=before.lower(); a=after.lower()
            if any(c.lower() in b[-50:] for c in hist_cues):
                return None

            # Negated ceiling/floor: preserve operator, let negation be a separate field.
            if re.search(r"(?:not\s+(?:expect|forecast).*?(?:above|exceed)|does\s+not.*?exceed)$",b[-55:]):
                return "greater_than"
            if re.search(r"(?:不会高于|不会超过|不预计.*超过|并不预计.*超过)$",before[-45:]):
                return "greater_than"

            c=detect_comparison(before[-42:])
            if c:
                return c

            # Postfix CJK predicates.
            aft=after[:22]
            if re.search(r"(?:を上回る|を超える|超となる|超を維持|以上)",aft):
                return "greater_than"
            if re.search(r"(?:を下回る|未満|以下)",aft):
                return "less_than"
            if re.search(r"(?:以上|高于|超过)",aft):
                return "greater_than"
            if re.search(r"(?:以下|低于)",aft):
                return "less_than"
            return None

        if kind=="direction":
            short_before=before[-28:].lower()
            short_after=after[:55].lower()
            # A "from X" value is the baseline, not the changed endpoint.
            if re.search(r"(?:\bfrom\s*|由\s*|から\s*)$",short_before):
                return None
            # Delta quantities carry the change direction; comparative historical
            # wording such as "25 bps above" also determines the sign.
            if q and q.get("unit")=="delta":
                d=detect_direction(around)
                if d:return d
                low=around.lower()
                if any(x in low for x in ["bps above","basis points above","percentage points above","个基点高","个百分点高","ベーシスポイント上"]):
                    return "increase"
                if any(x in low for x in ["bps below","basis points below","percentage points below","个基点低","个百分点低","ベーシスポイント下","パーセントポイント低"]):
                    return "decrease"
                return None
            # Endpoint explicitly governed by rose/fell/increased/decreased etc.
            d=detect_direction(before[-55:])
            if d and re.search(r"(?:\bto\s*|至\s*|到\s*|へ\s*)[^,;。]{0,12}$",short_before):
                return d
            # Direct predicates immediately before the value.
            d2=detect_direction(before[-35:])
            if d2:
                return d2
            # Constructions where the change is stated after the current value.
            if any(x in short_after for x in ["percentage points below","个百分点","パーセントポイント",
                                               "increase","growth","同比增长","増加","上昇","下降","低下"]):
                if any(x in short_after for x in ["below","下降","低下","減少"]):
                    return "decrease"
                if any(x in short_after for x in ["above","increase","growth","同比增长","増加","上昇","提升"]):
                    return "increase"
            # A fall/drop predicate or CJK below-threshold predicate can encode downside.
            if any(x in short_before for x in ["fall","drop","跌破","将低于","下回る","未満"]):
                return "decrease"
            return None
        return None

    def extract(self,text,language="en",reference_facts=None):
        # reference-independent. reference_facts deliberately ignored.
        entities=self.extract_entities(text,language)
        metrics=self.extract_metrics(text,language)
        terms=self.extract_terms(text,language)
        tickers=self.extract_tickers(text)
        acronyms=self.extract_acronyms(text)
        quantities=self.extract_quantities(text,language)
        times=self.extract_times(text,language)
        entity_overrides=self._sequence_entity_overrides(text,quantities,entities)
        metric_overrides=self._sequence_metric_overrides(text,quantities,metrics)

        facts=[]
        for q in quantities:
            clause=clause_for_span(text,q["span"])
            e_pool=self._same_clause_candidates(text,q["span"],entities) or entities
            m_pool=self._same_clause_candidates(text,q["span"],metrics) or metrics
            t_pool=self._same_clause_candidates(text,q["span"],times) or times
            ent=self._nearest(q["span"],e_pool,True)
            if q["span"][0] in entity_overrides:
                ent={"canonical":entity_overrides[q["span"][0]],"span":q["span"],"explicit":True}
            met=self._nearest(q["span"],m_pool,True)
            if q["span"][0] in metric_overrides:
                met={"canonical":metric_overrides[q["span"][0]],"span":q["span"],"explicit":True}
            if met:
                met=dict(met)
                met["canonical"]=self._specialized_metric(met["canonical"],q,text,language)
            tim=self._nearest(q["span"],t_pool,True)
            if t_pool:
                near=min(t_pool,key=lambda x:self._distance(q["span"],x["span"]))
                if self._distance(q["span"],near["span"]) <= 90:
                    tim=near
            ticker=self._nearest(q["span"],tickers,True)
            acronym=self._nearest(q["span"],acronyms,True)

            f={
                "fact_id":f"H{len(facts)+1}",
                "value":q["value"],"surface_value":q["surface"],
                "unit":q["unit"],"currency":q["currency"],
                "negation":self._local_operator(text,q["span"],"negation",q,language),
                "comparison":self._local_operator(text,q["span"],"comparison",q,language),
                "direction":self._local_operator(text,q["span"],"direction",q,language),
                "confidence":1.0,
                "clause_span":clause["span"]
            }
            if ent:f["entity"]=ent["canonical"]
            if met:f["metric"]=met["canonical"]
            if tim:f["time"]=tim["canonical"]
            if ticker:f["ticker"]=ticker["canonical"]
            if acronym:f["acronym"]=acronym["canonical"]
            facts.append(f)

        for t in terms:
            clause=clause_for_span(text,t["span"])
            e_pool=self._same_clause_candidates(text,t["span"],entities) or entities
            ent=self._nearest(t["span"],e_pool,True)
            tim=self._nearest(t["span"],times,True)
            f={"fact_id":f"H{len(facts)+1}","term":t["canonical"],
               "negation":detect_negation(clause["text"]),
               "comparison":detect_comparison(clause["text"]),
               "direction":detect_direction(clause["text"]),
               "confidence":0.9,"clause_span":clause["span"]}
            if ent:f["entity"]=ent["canonical"]
            if tim:f["time"]=tim["canonical"]
            facts.append(f)
        return facts
