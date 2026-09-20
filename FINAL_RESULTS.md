# FinASR-FER v0.6 Final Results and Reporting Policy

## Primary unbiased extractor validation
Use **v0.5 on Diverse-149** as the formal held-out result because v0.5 was frozen before Diverse-150 manual review / failure analysis.

- Entity F1: 90.77%
- Metric F1: 81.63%
- Value F1: 92.96%
- Time F1: 71.45%
- Core Fact F1: 78.87%
- Full Fact F1: 52.27%
- Entity-Metric-Value Binding Accuracy: 84.56%
- Perfect-transcript FER-Auto floor: 8.80%
- Positive negation accuracy: 100.0%
- Positive comparison accuracy: 66.67%
- Positive direction accuracy: 58.33%

## v0.6 final-release post-hoc diagnostics on Diverse-149
These are NOT a second held-out claim because Diverse-149 informed v0.6 development.

- Entity F1: 92.36%
- Metric F1: 89.81%
- Value F1: 94.59%
- Time F1: 72.31%
- Core Fact F1: 87.26%
- Full Fact F1: 58.60%
- Binding Accuracy: 91.95%
- Perfect-transcript FER-Auto floor (final v0.6 scorer): 8.22%
- Positive negation accuracy: 100.0%
- Positive comparison accuracy: 89.58%
- Positive direction accuracy: 58.33%

## Development data
Human-300 is treated as diagnostic/development data. It has substantially lower linguistic diversity than Diverse-149 and should not be used for the main generalization claim.

## FER v0.6
v0.6 adds a penalty for unmatched hypothesis facts (spurious financial facts), so hallucinated extra financial propositions increase FER.
