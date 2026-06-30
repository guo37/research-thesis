# 实验登记表

最后更新：2026-06-30

这里登记所有会影响论文论证的实验。每一行都应指向对应配置、代码、输出和结果解读。

## 实验列表

| ID | 名称 | 对应研究内容 | 状态 | 配置 | 输出 | 解读 |
| --- | --- | --- | --- | --- | --- | --- |
| Exp0 | ScienceQA 数据集诊断 | RC2 | 已完成 | [configs/exp0_scienceqa.yaml](../configs/exp0_scienceqa.yaml) | [reports/exp0_dataset_diagnosis](../reports/exp0_dataset_diagnosis) | [RESULT_INTERPRETATION.md](../reports/exp0_dataset_diagnosis/RESULT_INTERPRETATION.md) |
| Exp0.1 | 缺失类型标注结果 | RC2 | 标签分析已完成 | [configs/exp0_1_missing_type_annotation.yaml](../configs/exp0_1_missing_type_annotation.yaml) | [data/scienceqa/annotation](../data/scienceqa/annotation), [reports/exp0_1_missing_type_annotation](../reports/exp0_1_missing_type_annotation) | [human_label_analysis.md](../reports/exp0_1_missing_type_annotation/human_label_analysis.md) |
| Exp0.2 | 选择性补全门控基线 | RC2 | 分组压力测试与全量预测已完成 | [configs/exp0_2_selective_completion_gate.yaml](../configs/exp0_2_selective_completion_gate.yaml) | [reports/exp0_2_selective_completion_gate](../reports/exp0_2_selective_completion_gate) | [run_summary.md](../reports/exp0_2_selective_completion_gate/run_summary.md) |
| Exp1.0 | 教育多模态证据统一 schema | RC1/RC2/RC3 基础 | 三数据集样例已完成 | [configs/exp1_educational_mm_schema.yaml](../configs/exp1_educational_mm_schema.yaml) | [data/educational_mm/schema_samples](../data/educational_mm/schema_samples), [reports/exp1_educational_mm_schema](../reports/exp1_educational_mm_schema) | [schema_summary.md](../reports/exp1_educational_mm_schema/schema_summary.md) |
| Exp1.1 | 文本证据对齐检索 baseline | RC1 | 已完成 | [configs/exp1_1_text_evidence_retrieval.yaml](../configs/exp1_1_text_evidence_retrieval.yaml) | [reports/exp1_1_text_evidence_retrieval](../reports/exp1_1_text_evidence_retrieval) | [run_summary.md](../reports/exp1_1_text_evidence_retrieval/run_summary.md) |
| Exp1.2 | hard negative 与图像证据检索 | RC1 | 计划中 | 待定 | 待定 | 待定 |
| Exp2 | 模态必要性判断与鲁棒推理 | RC2 | ScienceQA pilot 已完成，主实验计划中 | 待定 | 待定 | 待定 |
| Exp3 | 证据约束的可解释教育推理 | RC3 | 计划中 | 待定 | 待定 | 待定 |

## Exp0 当前结论

ScienceQA 的图像缺失与教育元数据存在明显结构关联。当前证据：

- 总样本数：21,208。
- 图像缺失率：51.28%。
- `skill` 与 `has_image` 的互信息最高。
- 当前报告中，仅使用 `skill` 的预测模型已经达到接近完美的 AUC。

Exp0 工作性结论：

> RC2 可以继续按 `MNAR-aware selective completion` 推进，但在没有标注证据前，不能把 `has_image = 0` 直接当成 `structural_absence`。

## Exp0.1 当前结论

当前标注表包含 372 行，没有空白或非法的 `human_label`。

只看缺图样本：

- `structural_absence`: 230 / 322 (71.4%)
- `accidental_missing`: 92 / 322 (28.6%)
- `ambiguous`: 0 / 322 (0.0%)

工作性结论：

> 经过人工复核，原先的 `ambiguous` 样本应视为“需要图但缺图”的样本。RC2 当前任务是二分类模态必要性门控：`structural_absence` vs `accidental_missing`。

## Exp0.2 当前结论

第一版选择性补全门控基线在原始测试集划分上表现完美；新增分组压力测试后，结论需要更谨慎：

- 原始样本划分：最佳模型测试集正类 F1 = 1.0000。
- `skill_holdout`：文本模型测试集正类 F1 = 0.8000，Balanced accuracy = 0.8692。
- `topic_holdout`：测试集只有 1 条正类，不能作为稳定泛化结论；它暴露出当前正类标注过度集中在 biology topic。
- 全量 10,876 条缺图样本已生成门控伪标签，其中 529 条预测为 `need_completion_accidental_missing`，10,347 条预测为 `skip_structural_absence`。

工作性结论：

> 二分类 RC2 门控是可行的，且在未见 skill 的评测上有一定泛化信号；但 topic 级别正类样本太少，后续需要补充标注 biology 以外的疑似 `accidental_missing` 样本，并抽查全量预测中的高置信正负类。

## Exp1.0 当前结论

已建立新的教育图文证据统一 schema，并分别生成 ScienceQA、TQA / CK12 和 AI2D 的 200 条样例。

当前状态：

- ScienceQA 可映射到统一 schema，共 21,208 条。
- ScienceQA 样例：有图 100 条、无图 100 条。
- TQA / CK12 样例：通过 `notefill/ck12-tqa-instruction` 流式抽取，有图 100 条、无图 100 条。
- AI2D 样例：通过 `lmms-lab/ai2d-no-mask` 流式抽取 200 条 diagram QA 样本。
- TQA / CK12 当前使用公开 instruction 版，完整原图版仍可后续通过官方 1.6GB 包补齐。

工作性结论：

> 新主线已具备三数据集统一输入。下一步应进入 RC1：在统一 schema 上实现教育图文证据对齐检索 baseline。

## Exp1.1 当前结论

已完成 RC1 的最小文本证据检索 baseline。

主要结果：

- ScienceQA：TF-IDF Recall@1 = 0.8939，MRR = 0.9364；BM25 Recall@1 = 0.8737，MRR = 0.9282。
- TQA / CK12：BM25 Recall@1 = 0.8400，MRR = 0.9167，但样例中唯一文本证据只有 9 条，说明公开 instruction 版上下文粒度过粗。
- AI2D：当前 schema 没有 `text_context`，已在文本证据检索实验中跳过。

工作性结论：

> RC1 的文本证据检索流程已打通。下一步不能只继续提高 TF-IDF/BM25 指标，而应加入 same-topic / same-skill hard negative，并为 AI2D 实现图像/diagram 证据检索。

## 必需的运行记录模板

每次新增实验运行时，都应复制 [templates/experiment-run.md](templates/experiment-run.md) 到带日期的报告目录，并在解读结果前填写完整。
