# Missing Type Annotation Guidelines

## Goal

Label whether a ScienceQA item without an image is missing an educationally useful visual modality, or whether the item is naturally text-only.

## Labels

| label | definition | decision rule |
| --- | --- | --- |
| `observed` | The original item has an image. | Use for `has_image=1` reference samples. |
| `structural_absence` | The item can be understood and solved without an image; no image is pedagogically necessary. | The question is about language, definitions, abstract reasoning, factual recall, or text-only evidence. |
| `accidental_missing` | The item would normally benefit from or require a visual, but this record has no image. | The question asks about maps, diagrams, figures, object properties, spatial layout, or visual comparison, yet `has_image=0`. |
| `ambiguous` | It is unclear whether an image is necessary. | Use when a visual could help but the text still contains enough information, or when the item wording is underspecified. |

## Important Rule

Do not copy `suggested_missing_type` into `human_label` automatically. It is only a sampling hint based on topic/skill missing-rate statistics.

## Recommended Annotation Procedure

1. Read `question`, `choices`, `hint`, `lecture`, and `solution`.
2. Check `has_image`.
3. If `has_image=1`, label `observed` unless the row is clearly malformed.
4. If `has_image=0`, decide whether a visual is pedagogically necessary.
5. Use `label_confidence` with `high`, `medium`, or `low`.
6. Use `label_note` for short evidence, especially when disagreeing with `suggested_missing_type`.

## Examples

- Simile/metaphor, punctuation, grammar: usually `structural_absence`.
- Map reading, geography location, image comparison: often `accidental_missing` if `has_image=0`.
- Biology classification or physical properties: inspect the exact question; many are `ambiguous` because text may be sufficient but visuals can help.
