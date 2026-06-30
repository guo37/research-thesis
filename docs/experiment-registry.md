# Experiment Registry

Last updated: 2026-06-30

Register every experiment that affects the thesis argument. Each row should point to config, code, outputs, and interpretation.

## Experiments

| ID | Name | Research content | Status | Config | Outputs | Interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| Exp0 | ScienceQA dataset diagnosis | RC2 | Complete | [configs/exp0_scienceqa.yaml](../configs/exp0_scienceqa.yaml) | [reports/exp0_dataset_diagnosis](../reports/exp0_dataset_diagnosis) | [RESULT_INTERPRETATION.md](../reports/exp0_dataset_diagnosis/RESULT_INTERPRETATION.md) |
| Exp0.1 | Missing type annotation labels | RC2 | Label analysis complete | [configs/exp0_1_missing_type_annotation.yaml](../configs/exp0_1_missing_type_annotation.yaml) | [data/scienceqa/annotation](../data/scienceqa/annotation), [reports/exp0_1_missing_type_annotation](../reports/exp0_1_missing_type_annotation) | [human_label_analysis.md](../reports/exp0_1_missing_type_annotation/human_label_analysis.md) |
| Exp0.2 | Selective-completion gate baseline | RC2 | First baseline complete | [configs/exp0_2_selective_completion_gate.yaml](../configs/exp0_2_selective_completion_gate.yaml) | [reports/exp0_2_selective_completion_gate](../reports/exp0_2_selective_completion_gate) | [run_summary.md](../reports/exp0_2_selective_completion_gate/run_summary.md) |
| Exp1 | Concept-aware retrieval | RC1 | Planned | Pending | Pending | Pending |
| Exp2 | MNAR-aware selective completion | RC2 | Planned | Pending | Pending | Pending |
| Exp3 | Evidence-constrained explanation generation | RC3 | Planned | Pending | Pending | Pending |

## Exp0 Current Conclusion

ScienceQA image missingness is strongly structured by educational metadata. Current evidence:

- Total samples: 21,208.
- Image missing rate: 51.28%.
- `skill` has the strongest mutual information with `has_image`.
- Skill-only prediction reaches near-perfect AUC in the current report.

Exp0 working implication:

> RC2 can continue as `MNAR-aware selective completion`, but `has_image = 0` must not be treated as `structural_absence` without label evidence.

## Exp0.1 Current Conclusion

The current label table contains 372 rows and no blank or invalid `human_label` values.

Missing-image rows only:

- `structural_absence`: 230 / 322 (71.4%)
- `accidental_missing`: 92 / 322 (28.6%)
- `ambiguous`: 0 / 322 (0.0%)

Working implication:

> After manual review, the former ambiguous rows should be treated as image-needed missing samples. The RC2 task is a binary modality-necessity gate: `structural_absence` vs `accidental_missing`.

## Exp0.2 Current Conclusion

The first selective-completion gate baseline performs perfectly on the original test split.

Working implication:

> The binary RC2 gate is feasible, but the result is not yet final thesis evidence because topic/skill overlap may allow memorization. Add topic/skill grouped stress tests before applying the gate to all missing-image samples.

## Required Run Note Template

For every new run, copy [templates/experiment-run.md](templates/experiment-run.md) into a dated report folder and fill it before interpreting results.
