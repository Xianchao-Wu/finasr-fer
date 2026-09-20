from finasr_fer import FinancialFactExtractor, StructuredFEREvaluator
import json

extractor=FinancialFactExtractor()

text="In FY2027 Q2, NVIDIA reported revenue of $30 billion and gross margin of 70 percent."
print(json.dumps(extractor.extract(text,"en"),ensure_ascii=False,indent=2))
