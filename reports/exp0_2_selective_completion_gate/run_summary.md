# Exp0.2 Selective-Completion Gate Baseline

Target:

```text
0 = structural_absence
1 = image_needed_missing = accidental_missing
```

## Data

- Rows used: 322 missing-image labeled candidates.
- Label counts: `{"accidental_missing": 92, "structural_absence": 230}`.
- Target counts: `{"0": 230, "1": 92}`.

## Metrics

| model | split | threshold | n | positive_rate | balanced_accuracy | macro_f1 | positive_f1 | positive_precision | positive_recall | pr_auc | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| majority | validation |  | 74 | 0.2973 | 0.5000 | 0.4127 | 0.0000 | 0.0000 | 0.0000 | 0.2973 | 52 | 0 | 22 | 0 |
| majority | test |  | 58 | 0.2931 | 0.5000 | 0.4141 | 0.0000 | 0.0000 | 0.0000 | 0.2931 | 41 | 0 | 17 | 0 |
| metadata | validation | 0.5000 | 74 | 0.2973 | 0.9808 | 0.9685 | 0.9565 | 0.9167 | 1.0000 | 0.9941 | 50 | 2 | 0 | 22 |
| metadata | test | 0.5000 | 58 | 0.2931 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 41 | 0 | 0 | 17 |
| text | validation | 0.3500 | 74 | 0.2973 | 0.9808 | 0.9685 | 0.9565 | 0.9167 | 1.0000 | 0.9878 | 50 | 2 | 0 | 22 |
| text | test | 0.3500 | 58 | 0.2931 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 41 | 0 | 0 | 17 |
| metadata_text | validation | 0.3500 | 74 | 0.2973 | 0.9808 | 0.9685 | 0.9565 | 0.9167 | 1.0000 | 0.9941 | 50 | 2 | 0 | 22 |
| metadata_text | test | 0.3500 | 58 | 0.2931 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 41 | 0 | 0 | 17 |

## Split Overlap Check

| Field | Split | Unique values | Unseen from train | Examples |
| --- | --- | --- | --- | --- |
| topic | validation | 16 | 0 |  |
| topic | test | 16 | 1 | reading-comprehension |
| skill | validation | 50 | 21 | Antebellum Period: economies of the North and South, Changes to Earth's surface: earthquakes, Changes to Earth's surface: erosion, Choose metric units of mass, Classify changes to Earth's surface |
| skill | test | 39 | 16 | Banks, Benjamin Franklin, Choose customary units of volume, Formatting titles, Identify elementary substances and compounds using chemical formulas |

If validation/test topics or skills are mostly seen in train, high scores may partly reflect topic/skill memorization. Add a grouped stress test before presenting final thesis evidence.

## Current Best Test Result

- Best model by positive F1: `metadata`.
- Positive F1: `1.0000`.
- PR-AUC: `1.0000`.
- Balanced accuracy: `1.0000`.
- Confusion matrix on test: TN=41, FP=0, FN=0, TP=17.

## Interpretation

- This is a small labeled set, so the result is a feasibility signal, not final thesis evidence.
- This supports framing RC2 as a modality-necessity gate: skip structural absence, handle accidental missingness.
- If these labels are auto-assisted, manually review sampled positive rows before using this as a thesis result.
