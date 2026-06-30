# Exp0.1 Human Label Analysis

Generated from `data/scienceqa/annotation/missing_type_annotation_candidates.csv`.

## Data Quality

| Check | Value |
| --- | --- |
| Total rows | 372 |
| Missing-image rows | 322 |
| Blank `human_label` | 0 |
| Invalid labels | 0 |
| Image/label consistency issues | 0 |

## Label Distribution

| Label | Count | Share of all rows |
| --- | --- | --- |
| observed | 50 | 13.4% |
| structural_absence | 230 | 61.8% |
| accidental_missing | 1 | 0.3% |
| ambiguous | 91 | 24.5% |

Missing-image rows only:

| Label | Count | Share of missing-image rows |
| --- | --- | --- |
| structural_absence | 230 | 71.4% |
| accidental_missing | 1 | 0.3% |
| ambiguous | 91 | 28.3% |

## Suggested Type vs Human Label

| Suggested type | Total | observed | structural_absence | accidental_missing | ambiguous |
| --- | --- | --- | --- | --- | --- |
| structural_absence_candidate | 150 | 0 | 150 | 0 | 0 |
| ambiguous_missing_candidate | 100 | 0 | 8 | 1 | 91 |
| accidental_missing_candidate | 72 | 0 | 72 | 0 | 0 |
| observed_reference | 50 | 50 | 0 | 0 | 0 |

## Subject vs Human Label

| Subject | Total | observed | structural_absence | accidental_missing | ambiguous |
| --- | --- | --- | --- | --- | --- |
| natural science | 204 | 30 | 83 | 0 | 91 |
| social science | 92 | 17 | 74 | 1 | 0 |
| language science | 76 | 3 | 73 | 0 | 0 |

## Split vs Human Label

| Split | Total | observed | structural_absence | accidental_missing | ambiguous |
| --- | --- | --- | --- | --- | --- |
| train | 223 | 33 | 137 | 1 | 52 |
| validation | 84 | 10 | 52 | 0 | 22 |
| test | 65 | 7 | 41 | 0 | 17 |

## Top Topics

| Topic | Total | observed | structural_absence | accidental_missing | ambiguous |
| --- | --- | --- | --- | --- | --- |
| biology | 138 | 10 | 38 | 0 | 90 |
| us-history | 45 | 2 | 43 | 0 | 0 |
| geography | 26 | 14 | 12 | 0 | 0 |
| figurative-language | 22 | 0 | 22 | 0 | 0 |
| physics | 22 | 8 | 14 | 0 | 0 |
| writing-strategies | 19 | 1 | 18 | 0 | 0 |
| chemistry | 15 | 3 | 11 | 0 | 1 |
| reference-skills | 13 | 0 | 13 | 0 | 0 |
| world-history | 12 | 0 | 12 | 0 | 0 |
| units-and-measurement | 11 | 0 | 11 | 0 | 0 |
| earth-science | 8 | 4 | 4 | 0 | 0 |
| punctuation | 8 | 0 | 8 | 0 | 0 |
| economics | 7 | 1 | 5 | 1 | 0 |
| literacy-in-science | 5 | 0 | 5 | 0 | 0 |
| science-and-engineering-practices | 5 | 5 | 0 | 0 | 0 |

## Confidence Distribution

| Confidence band | Count |
| --- | --- |
| >=0.90 | 124 |
| 0.80-0.89 | 149 |
| 0.70-0.79 | 8 |
| <0.70 | 91 |
| <blank> | 0 |
| invalid | 0 |

## Interpretation

- Among missing-image rows, `230` / `322` (71.4%) are labeled `structural_absence`.
- Among missing-image rows, `92` / `322` (28.6%) are `ambiguous` or `accidental_missing`, so they should be treated as review/completion candidates rather than automatically completed.
- `accidental_missing` has only 1 labeled row, so a four-class supervised classifier is not currently defensible.
- The next RC2 task should be a selective-completion gate: predict `structural_absence` vs `review_or_completion_needed` for missing-image samples.
- Ambiguity is concentrated in natural-science/biology rows, which suggests the gate should use topic/skill plus question text rather than subject alone.

## Recommended Next Experiment

Define `review_or_completion_needed = accidental_missing OR ambiguous` for missing-image rows.

Run an Exp0.2 baseline comparison:

1. Majority baseline.
2. Metadata-only logistic regression: subject, topic, skill, grade, text length.
3. Text-only TF-IDF logistic regression: question, choices, hint, lecture, solution.
4. Metadata + text TF-IDF logistic regression.

Report balanced accuracy, macro F1, positive-class F1, PR-AUC, and confusion matrix.

If Exp0.2 can identify `review_or_completion_needed` above baseline, RC2 can continue as `MNAR-aware selective completion`. If not, RC2 should be narrowed to descriptive MNAR diagnosis plus rule-assisted modality necessity analysis.
