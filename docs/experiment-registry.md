# Experiment Registry

Last updated: 2026-06-30

Register every experiment that affects the thesis argument. Each row should point to config, code, outputs, and interpretation.

## Experiments

| ID | Name | Research content | Status | Config | Outputs | Interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| Exp0 | ScienceQA dataset diagnosis | RC2 | Complete | [configs/exp0_scienceqa.yaml](../configs/exp0_scienceqa.yaml) | [reports/exp0_dataset_diagnosis](../reports/exp0_dataset_diagnosis) | [RESULT_INTERPRETATION.md](../reports/exp0_dataset_diagnosis/RESULT_INTERPRETATION.md) |
| Exp0.1 | Missing type annotation candidates | RC2 | Candidate table complete, manual labels pending | [configs/exp0_1_missing_type_annotation.yaml](../configs/exp0_1_missing_type_annotation.yaml) | [data/scienceqa/annotation](../data/scienceqa/annotation), [reports/exp0_1_missing_type_annotation](../reports/exp0_1_missing_type_annotation) | Pending after human labels |
| Exp1 | Concept-aware retrieval | RC1 | Planned | Pending | Pending | Pending |
| Exp2 | MNAR-aware selective completion | RC2 | Planned | Pending | Pending | Pending |
| Exp3 | Evidence-constrained explanation generation | RC3 | Planned | Pending | Pending | Pending |

## Exp0 Current Conclusion

ScienceQA image missingness is strongly structured by educational metadata. Current evidence:

- Total samples: 21,208.
- Image missing rate: 51.28%.
- `skill` has the strongest mutual information with `has_image`.
- Skill-only prediction reaches near-perfect AUC in the current report.

Working implication:

> RC2 can continue as `MNAR-aware selective completion`, but `has_image = 0` must not be treated as `structural_absence` until Exp0.1 human labels are finished.

## Required Run Note Template

For every new run, copy [templates/experiment-run.md](templates/experiment-run.md) into a dated report folder and fill it before interpreting results.

