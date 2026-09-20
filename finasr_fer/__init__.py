from .evaluator import StructuredFEREvaluator, evaluate_pair, evaluate_dataset, aggregate_fer
from .parser import FinancialFactExtractor, FinancialOntology
from .llm_extractor import LLMFinancialFactExtractor
from .alignment import align_facts
from .normalization import (
    normalize_text, normalize_number_surface, parse_financial_quantity,
    canonicalize_money, value_distance
)
from .metrics import word_error_rate, char_error_rate
from .perturbation import evaluate_perturbation_set
from .consistency import evaluate_derived_constraints
from .extractor_eval import evaluate_extractor

__version__ = "0.7.1"

from .extractor_eval_covered import evaluate_extractor_gold_covered

from .extractor_eval_protocol import evaluate_extractor_protocol
