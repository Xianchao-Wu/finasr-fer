import argparse,json
from .io import read_jsonl,read_hypotheses_jsonl
from .evaluator import evaluate_dataset
from .perturbation import evaluate_perturbation_set
from .parser import FinancialFactExtractor
from .extractor_eval import evaluate_extractor

def main():
    p=argparse.ArgumentParser(prog="finasr-fer")
    sub=p.add_subparsers(dest="cmd",required=True)
    e=sub.add_parser("evaluate")
    e.add_argument("--references",required=True);e.add_argument("--hypotheses",required=True);e.add_argument("--output")
    q=sub.add_parser("perturbations")
    q.add_argument("--input",required=True);q.add_argument("--output")
    x=sub.add_parser("extract")
    x.add_argument("--text",required=True);x.add_argument("--language",default="en",choices=["en","zh","ja"])
    z=sub.add_parser("extractor-eval")
    z.add_argument("--input",required=True);z.add_argument("--output")
    a=p.parse_args()

    if a.cmd=="evaluate":
        res=evaluate_dataset(read_jsonl(a.references),read_hypotheses_jsonl(a.hypotheses))
    elif a.cmd=="perturbations":
        res=evaluate_perturbation_set(read_jsonl(a.input))
    elif a.cmd=="extractor-eval":
        res=evaluate_extractor(read_jsonl(a.input))
    else:
        res=FinancialFactExtractor().extract(a.text,a.language)

    txt=json.dumps(res,ensure_ascii=False,indent=2)
    if getattr(a,"output",None):open(a.output,"w",encoding="utf-8").write(txt)
    else:print(txt)
if __name__=="__main__":main()
