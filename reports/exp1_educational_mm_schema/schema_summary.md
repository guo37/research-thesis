# Exp1.0 教育多模态证据统一 Schema

## 目标

将 ScienceQA、TQA/CK12 和 AI2D 映射到同一套教育图文证据 schema，为后续 RC1 证据对齐检索、RC2 模态必要性判断和 RC3 证据约束推理提供统一输入。

## 数据集状态

| dataset | local_status | sample_count | has_image_count | text_context_coverage | next_action |
| --- | --- | --- | --- | --- | --- |
| ScienceQA | 已接入 | 21208 | 10332 | 0.993 | 作为统一 schema 和 RC1/RC2 pilot 数据 |
| TQA / CK12 | 待接入 |  |  |  | 把原始文件放入 data\tqa\raw 后编写 adapter |
| AI2D | 待接入 |  |  |  | 把原始文件放入 data\ai2d\raw 后编写 adapter |

## 统一字段

| column |
| --- |
| dataset |
| sample_id |
| original_id |
| split |
| question |
| choices |
| answer |
| text_context |
| image_ref |
| has_image |
| subject |
| topic |
| skill |
| evidence_type |
| modality_case |
| answer_format |
| source_task |

## 字段映射计划

| schema_column | ScienceQA | TQA | AI2D |
| --- | --- | --- | --- |
| question | question | question | question |
| choices | choices_json | answer choices | answer choices |
| answer | answer | answer | correct answer |
| text_context | hint + lecture + solution | textbook paragraph | diagram metadata / optional text |
| image_ref | image_ref | figure / diagram path | diagram image path |
| topic | topic | chapter / lesson | diagram topic if available |
| skill | skill | learning objective if available | question category if available |

## ScienceQA 字段覆盖率

| column | non_empty | coverage |
| --- | --- | --- |
| dataset | 21208 | 1.0 |
| sample_id | 21208 | 1.0 |
| original_id | 21208 | 1.0 |
| split | 21208 | 1.0 |
| question | 21208 | 1.0 |
| choices | 21208 | 1.0 |
| answer | 21208 | 1.0 |
| text_context | 21060 | 0.993 |
| image_ref | 10332 | 0.4872 |
| has_image | 21208 | 1.0 |
| subject | 21208 | 1.0 |
| topic | 21208 | 1.0 |
| skill | 21208 | 1.0 |
| evidence_type | 21208 | 1.0 |
| modality_case | 21208 | 1.0 |
| answer_format | 21208 | 1.0 |
| source_task | 21208 | 1.0 |

## 输出

- ScienceQA schema sample：`data\educational_mm\schema_samples\scienceqa_schema_sample.csv`

## 下一步

1. 接入 TQA / CK12，本地抽取 100-200 条样本映射到同一 schema。
2. 接入 AI2D，本地抽取 100-200 条 diagram QA 样本映射到同一 schema。
3. 基于统一 schema 实现 RC1 的 BM25 / Sentence-BERT / CLIP 检索基线。
