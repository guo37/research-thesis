# RC2 Next Step Plan

Last updated: 2026-06-30

## Current Evidence

Exp0 showed that ScienceQA image missingness is strongly structured by subject/topic/skill metadata.

Exp0.1 label analysis shows:

- 372 labeled candidate rows.
- 322 missing-image rows.
- 230 / 322 missing-image rows are labeled `structural_absence`.
- 92 / 322 missing-image rows are labeled `accidental_missing`.
- 0 / 322 missing-image rows remain labeled `ambiguous`.

## Decision

Use a binary RC2 gate:

```text
structural_absence = skip completion
accidental_missing = image needed but missing
```

This keeps the thesis claim defensible:

> Education multimodal resources contain structured missingness; selective completion should first decide whether the missing modality is pedagogically necessary or worth reviewing, instead of completing all missing modalities.

## Exp0.2 Design

Input:

```text
data/scienceqa/annotation/missing_type_annotation_candidates.csv
```

Rows:

- Use only `has_image = 0`.

Target:

```text
y = 1 if human_label == accidental_missing
y = 0 if human_label == structural_absence
```

Baselines:

1. Majority baseline.
2. Metadata-only model: subject, topic, skill, grade, text_length.
3. Text-only model: question, choices, hint, lecture, solution.
4. Metadata + text model.

Metrics:

- Balanced accuracy.
- Macro F1.
- Positive-class F1.
- PR-AUC.
- Confusion matrix.

Minimum success condition:

> Metadata + text must beat majority and metadata-only baselines on positive-class F1 or PR-AUC.

## Exp0.2 First Result

The first baseline run on the original ScienceQA split reached perfect test metrics.

This should be treated as a feasibility signal, not final thesis evidence, because topic/skill overlap may make the task easier than a true generalization test.

Next validation:

1. Hold out entire topics.
2. Hold out entire skills where label counts permit.
3. Compare metadata-only, text-only, and metadata+text under the grouped split.
4. Only then apply the gate to all missing-image ScienceQA rows.

## Before Thesis Use

Before thesis use, spot-check:

1. A sample of `accidental_missing` rows.
2. A sample of `structural_absence` rows from language/social/natural science.
3. Any rows with unusual topic/skill combinations.
