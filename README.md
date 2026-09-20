# Structured Financial Error Rate (FER)

**Structured Financial Error Rate (FER)** is an evaluation metric designed for **financial automatic speech recognition (ASR)**.

Conventional metrics such as Word Error Rate (WER) and Character Error Rate (CER) treat recognition errors largely uniformly. In financial speech, however, errors can have very different consequences. For example:

> Reference: **Revenue was $12.6 billion.**
> Hypothesis: **Revenue was $126 billion.**

The two transcripts differ only locally, but the hypothesis introduces a **10× numerical error**.

FER evaluates ASR outputs at the level of **structured financial facts**, explicitly modeling numerical magnitude, financial entities, entity–metric–value bindings, temporal information, and semantic operators such as negation and comparison.

FER is bounded in:

$$
0 \leq \mathrm{FER} \leq 1,
$$

where **lower is better**.

---

## Overview

The FER evaluation pipeline is:

```text
Reference + ASR Hypothesis
            |
            v
  Financial Fact Extraction
            |
            v
       Canonicalization
            |
            v
        Fact Alignment
            |
            v
 Component Errors + Severity Weights
            |
            v
         FER [0,1]
```

At a high level, FER consists of four stages:

1. Extract structured financial facts from the reference and ASR hypothesis.
2. Canonicalize numerical values and financial fields.
3. Align reference and hypothesis facts using minimum-cost matching.
4. Compute a severity-weighted structured error score, including missing and spurious financial facts.

---

## Financial Fact Representation

FER represents each financial fact as

$$
f=(e,m,v,u,c,t,n,o,d),
$$

where:

| Symbol | Component             | Example                    |
| ------ | --------------------- | -------------------------- |
| \(e\)  | Entity                | Apple                      |
| \(m\)  | Financial metric      | revenue                    |
| \(v\)  | Normalized value      | \(12.6\times10^9\)         |
| \(u\)  | Unit                  | billion                    |
| \(c\)  | Currency              | USD                        |
| \(t\)  | Fiscal/temporal scope | Q1                         |
| \(n\)  | Negation              | not / none                 |
| \(o\)  | Comparison operator   | above / below / none       |
| \(d\)  | Direction             | increase / decrease / none |

For example:

> **Apple reported revenue of $12.6 billion in Q1.**

can be represented as approximately:

```text
(
  entity   = Apple,
  metric   = revenue,
  value    = 12.6e9,
  unit     = billion,
  currency = USD,
  time     = Q1,
  negation = none,
  operator = none,
  direction= none
)
```

FER additionally considers the **entity–metric–value binding**, since correctly recognizing an entity and a number is insufficient if the number is attached to the wrong company or financial metric.

---

## Magnitude-Aware Numerical Errors

A key design goal of FER is to distinguish small numerical deviations from catastrophic magnitude errors.

For reference value \(v\) and hypothesis value \(\hat v\), FER uses a logarithmic magnitude-aware error:

$$
E_v(v,\hat v)
=
\min\left(
1,
\frac{
|\log(|v|+\epsilon)-\log(|\hat v|+\epsilon)|
}{\tau}
\right).
$$

By default,

$$
\tau=\log 10.
$$

Therefore, a **10× magnitude error** reaches the maximum numerical penalty, while smaller multiplicative deviations receive proportionally smaller penalties.

This makes FER sensitive to errors such as:

```text
$12.6 billion  ->  $126 billion
```

that may appear small under conventional lexical metrics but substantially change the underlying financial proposition.

---

## Severity-Weighted Structured Errors

FER does not treat all financial components equally.

The default scoring places greater emphasis on errors that can substantially change financial meaning, including:

* numerical value,
* entity–metric–value binding,
* negation,
* comparison,
* direction.

Lower weights are assigned to components such as entity, metric, unit, currency, and temporal scope according to their role in the structured fact.

The current default weights are:

| Component  | Weight |
| ---------- | -----: |
| Entity     |    1.0 |
| Metric     |    1.0 |
| Value      |    2.5 |
| Unit       |    1.5 |
| Currency   |    1.5 |
| Time       |    1.5 |
| Negation   |    2.5 |
| Comparison |    2.5 |
| Direction  |    2.0 |
| Binding    |    2.5 |

These weights can be modified for different evaluation settings.

---

## Missing and Spurious Financial Facts

FER explicitly handles both:

**Missing facts**

A financial fact present in the reference but absent from the ASR hypothesis receives its full active financial-information penalty.

**Spurious facts**

A financial fact appearing in the hypothesis but not supported by the reference receives a spurious-fact penalty.

The default spurious-fact weight is:

```text
lambda_spur = 2.5
```

The final normalization guarantees:

$$
0\leq \mathrm{FER}\leq1.
$$

FER can therefore be interpreted as the fraction of financially relevant structured information corrupted by the ASR output.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/finasr-fer.git
cd finasr-fer
```

Install the package:

```bash
pip install -e .
```

For development:

```bash
pip install -e .
pytest
```

---

## Repository Structure

```text
finasr-fer/
├── README.md
├── CHANGELOG.md
├── FINAL_RESULTS.md
├── REGRESSION_CHECK.md
├── V0_7_1_NOTES.md
├── pyproject.toml
│
├── finasr_fer/
│   ├── __init__.py
│   └── ...
│
├── scripts/
│   └── ...
│
├── tests/
│   └── ...
│
├── example_v0_3.py
└── schema_example.json
```

The core FER implementation is located in:

```text
finasr_fer/
```

Additional evaluation and extraction utilities are provided under:

```text
scripts/
```

---

## Quick Start

A minimal example is provided in:

```text
example_v0_3.py
```

Run:

```bash
python example_v0_3.py
```

A structured fact example is also provided in:

```text
schema_example.json
```

---

## Financial Fact Extraction with an LLM

FER requires structured financial facts for both the reference and hypothesis transcripts.

For automatic evaluation, this repository supports an LLM-based extraction pipeline. In our current pipeline, a locally hosted **Qwen-family instruction model** is used to convert financial transcripts into structured facts.

Conceptually:

```text
ASR transcript
      |
      v
Local LLM
      |
      v
Structured financial facts
      |
      v
FER
```

A local OpenAI-compatible inference server can be launched with vLLM.

A typical setup is:

```bash
vllm serve MODEL_PATH \
    --host 0.0.0.0 \
    --port 8000
```

The exact model name, serving arguments, and extraction scripts may depend on the local environment. See the scripts included in this repository for the configuration used by the current FER version.

### Extraction Output

The extractor should return structured facts containing fields corresponding to:

```json
{
  "entity": "Apple",
  "metric": "revenue",
  "value": 12600000000,
  "unit": "billion",
  "currency": "USD",
  "time": "Q1",
  "negation": null,
  "comparison": null,
  "direction": null
}
```

The FER implementation subsequently canonicalizes and aligns these facts before scoring.

---

## Example: Why FER Differs from WER

Consider:

```text
Reference:
Apple reported revenue of $12.6 billion.

Hypothesis A:
Apple reported revenue of $126 billion.

Hypothesis B:
Apple reported the revenue of $12.6 billion.
```

A conventional edit-distance metric may assign comparable or relatively small penalties to localized changes.

Financially, however, the two hypotheses are fundamentally different.

**Hypothesis A** changes the financial value by a factor of ten.

**Hypothesis B** largely preserves the financial proposition.

FER is designed to reflect this distinction by evaluating the underlying structured financial information rather than treating every lexical edit uniformly.

---

## Multilingual Evaluation

FER is designed to support multilingual financial ASR.

Our current experiments focus on:

* English (EN)
* Mandarin Chinese (ZH)
* Japanese (JA)

Surface forms are canonicalized before structured comparison. For example, equivalent representations of monetary values can be mapped into a common numerical and currency representation.

This allows FER to evaluate financial facts rather than relying only on language-specific surface strings.

---

## FinASR-Bench

FER is evaluated together with **FinASR-Bench**, a multilingual benchmark for financially critical ASR.

FinASR-Bench covers twelve error-sensitive challenge categories:

| Challenge                           | Distribution |
| ----------------------------------- | -----------: |
| Numbers / currency / percentage     |          15% |
| Financial terms                     |          10% |
| Acronyms                            |           8% |
| Company / ticker / entity names     |           7% |
| Number–unit–term composition        |          10% |
| Financial entity relations          |          12% |
| Confusable financial words          |           5% |
| Dates / fiscal periods              |           6% |
| Code-switching                      |           5% |
| Colloquial finance                  |           4% |
| Negation / condition / comparison   |          10% |
| Long-context multi-entity reasoning |           8% |

The benchmark contains both **real-world speech** and **controlled synthetic financial speech**, with experiments conducted in English, Chinese, and Japanese.

Benchmark data and additional release information will be provided separately.

---

## Human Validation

The severity design of FER was evaluated using an independent human study.

The current study contains:

* 120 controlled reference–hypothesis pairs,
* 10 financial error categories,
* 3 independent annotators,
* a five-point financial-severity scale.

The study includes benign lexical changes as well as financially consequential errors involving numerical magnitude, units, entity–value binding, financial metrics, fiscal time, direction, negation, and comparison.

Human ratings are used to examine whether FER better reflects financially consequential errors than conventional lexical or general-purpose semantic similarity metrics.

See the accompanying paper for the complete experimental setup and statistical analysis.

---

## Version

Current development version:

```text
FER v0.7.1
```

See:

```text
CHANGELOG.md
V0_7_1_NOTES.md
REGRESSION_CHECK.md
```

for implementation changes and regression information.

For experiments intended to reproduce paper results, we recommend using a tagged release rather than the latest development branch.

---

## Reproducibility

To reproduce a specific FER version:

```bash
git checkout v0.7.1
```

Run the regression tests:

```bash
pytest
```

and consult:

```text
REGRESSION_CHECK.md
FINAL_RESULTS.md
```

for version-specific evaluation information.

---

## Citation

If you use FER or FinASR-Bench in academic work, please cite our paper:

```bibtex
@inproceedings{fer2027,
  title     = {Structured Financial Error Rate for Financial ASR},
  author    = {TBD},
  booktitle = {Proceedings of the IEEE International Conference on
               Acoustics, Speech and Signal Processing (ICASSP)},
  year      = {2027}
}
```

The citation information will be updated after publication.

---

## License

Please see the `LICENSE` file for licensing information.

---

## Disclaimer

FER is an evaluation metric for research on financial-domain speech recognition. It measures discrepancies between structured financial information extracted from reference and ASR hypothesis transcripts.

FER scores should be interpreted together with conventional transcription metrics such as WER/CER and, where appropriate, additional semantic or task-specific evaluation measures.

