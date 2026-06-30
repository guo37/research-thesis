# Exp1.0 教育多模态证据统一 Schema

## 目标

将 ScienceQA、TQA/CK12 和 AI2D 映射到同一套教育图文证据 schema，为后续 RC1 证据对齐检索、RC2 模态必要性判断和 RC3 证据约束推理提供统一输入。

## 数据集状态

| dataset | local_status | sample_count | has_image_count | text_context_coverage | next_action |
| --- | --- | --- | --- | --- | --- |
| ScienceQA | 已接入本地处理表 | 21208 | 10332 | 0.993 | 作为统一 schema 和 RC1/RC2 pilot 数据 |
| TQA / CK12 | HF 流式样例：notefill/ck12-tqa-instruction | 200 | 100 | 1.0 | 后续可下载官方完整包补齐原图路径 |
| AI2D | HF 流式样例：lmms-lab/ai2d-no-mask | 200 | 200 | 0.0 | 作为 diagram QA 证据对齐和 wrong-image 实验数据 |

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
| text_context | hint + lecture + solution | lesson + instruction; official package can add textbook paragraph | diagram metadata / optional text |
| image_ref | image_ref | figure / diagram path | diagram image path |
| topic | topic | chapter / lesson | diagram topic if available |
| skill | skill | learning objective if available | question category if available |

## 字段覆盖率

| column | ScienceQA | TQA_CK12 | AI2D |
| --- | --- | --- | --- |
| dataset | 1.0 | 1.0 | 1.0 |
| sample_id | 1.0 | 1.0 | 1.0 |
| original_id | 1.0 | 1.0 | 1.0 |
| split | 1.0 | 1.0 | 1.0 |
| question | 1.0 | 1.0 | 1.0 |
| choices | 1.0 | 1.0 | 1.0 |
| answer | 1.0 | 1.0 | 1.0 |
| text_context | 0.993 | 1.0 | 0.0 |
| image_ref | 0.4872 | 0.5 | 1.0 |
| has_image | 1.0 | 1.0 | 1.0 |
| subject | 1.0 | 1.0 | 1.0 |
| topic | 1.0 | 1.0 | 1.0 |
| skill | 1.0 | 1.0 | 1.0 |
| evidence_type | 1.0 | 1.0 | 1.0 |
| modality_case | 1.0 | 1.0 | 1.0 |
| answer_format | 1.0 | 1.0 | 1.0 |
| source_task | 1.0 | 1.0 | 1.0 |

## 输出

- ScienceQA schema sample：`data\educational_mm\schema_samples\scienceqa_schema_sample.csv`
- TQA / CK12 schema sample：`data\educational_mm\schema_samples\tqa_ck12_schema_sample.csv`
- AI2D schema sample：`data\educational_mm\schema_samples\ai2d_schema_sample.csv`

## 下一步

1. 检查 TQA / CK12 样例中的 `has_image=1` 覆盖情况；如果不足，下载官方完整 TQA 包补齐 diagram 图像路径。
2. 用 AI2D 构造 wrong-image hard negative，作为 RC1 和 RC2 的第一批鲁棒性实验。
3. 基于统一 schema 实现 RC1 的 BM25 / Sentence-BERT / CLIP 检索基线。
