# Exp0.1 Auto Label Summary

Generated: 2026-06-30

> Superseded by manual review: the 91 auto-labeled `ambiguous` rows were reviewed and relabeled as `accidental_missing` because they need images but `has_image=0`. Use `human_label_analysis.md` as the current label evidence.

## Method

A conservative rule-assisted model pass filled `human_label`, `label_confidence`, and `label_note` in `data/scienceqa/annotation/missing_type_annotation_candidates.csv`. The intermediate auto-labeled copy remains available at `data/scienceqa/annotation/missing_type_annotation_candidates_auto_labeled.csv` for audit.

Decision policy:

- `observed`: `has_image=1`.
- `accidental_missing`: explicit visual/material cue is present but `has_image=0`.
- `structural_absence`: the question and choices are sufficient as text, with no explicit visual dependency.
- `ambiguous`: visual support may be relevant or the missing type cannot be decided confidently from text alone.

These are pre-labels, not final adjudicated labels. Review low-confidence rows before using the distribution as thesis evidence.

## Label Distribution

| Label | Count |
| --- | ---: |
| observed | 50 |
| structural_absence | 230 |
| accidental_missing | 1 |
| ambiguous | 91 |

## Confidence Distribution

| Confidence band | Count |
| --- | ---: |
| >=0.90 | 124 |
| 0.80-0.89 | 149 |
| 0.70-0.79 | 8 |
| <0.70 | 91 |

## Original Sampling Hints

| Suggested type | Count |
| --- | ---: |
| structural_absence_candidate | 150 |
| ambiguous_missing_candidate | 100 |
| accidental_missing_candidate | 72 |
| observed_reference | 50 |

## Review Queue

Review rows are written to `reports/exp0_1_missing_type_annotation/auto_label_review_queue.csv`.

Recommended review priority:

1. All `accidental_missing` rows.
2. All `ambiguous` rows.
3. All rows with confidence below 0.80.
4. A random sample from `structural_absence` rows, especially natural-science classification items.

