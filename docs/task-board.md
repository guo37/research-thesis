# 研究任务看板

最后更新：2026-06-30

这个文件只维护短期操作队列。复杂推理应写入对应实验、论文或组会文件。

## 当前

- [x] 完成 `data/scienceqa/annotation/missing_type_annotation_candidates.csv` 的 Exp0.1 标注。
- [x] 汇总 Exp0.1 标签分布，并判断 RC2 是否继续按 `MNAR-aware selective completion` 推进。
- [x] 将 91 条需要图的原 `ambiguous` 样本重标为 `accidental_missing`。
- [ ] 论文使用前，抽查一部分正类 `accidental_missing` 和负类 `structural_absence` 样本。
- [x] 实现 Exp0.2 选择性补全门控：预测 `structural_absence` vs `accidental_missing`。
- [x] 为 Exp0.2 增加按 topic 或 skill 留出的分组压力测试。
- [x] 将 Exp0.2 门控应用到全部 ScienceQA 缺图样本，生成伪标签排序清单。
- [ ] 抽查 `full_missing_predictions.csv` 中高置信 `need_completion_accidental_missing` 与高置信 `skip_structural_absence` 样本。
- [ ] 选择一个规范论文大纲文件，并把旧大纲中不再适用的内容标为 preliminary。
- [ ] 基于 Exp0 和 Exp0.1 准备下一次两周组会总结。

## 下一步

- [ ] 围绕 topic 级别正类过度集中问题，补充抽样标注 biology 以外的潜在 `accidental_missing` 样本。
- [ ] 将文献综述扩展到 30-40 篇论文。
- [ ] 构建最小教育知识图谱：concept、resource、belongs_to、same_skill、prerequisite、related。
- [ ] 定义 RC1 基线：CLIP、CLIP + adapter、ordinary contrastive、random hard negative、same-subject hard negative、concept-aware hard negative。
- [ ] 定义 RC3 的 100 条解释评测集 schema。

## 后续

- [ ] 增加 RC1 检索实验脚本和配置。
- [ ] 增加 RC2 选择性补全基线和消融计划。
- [ ] 增加 RC3 解释生成脚本和评测报告。
- [ ] 将稳定的组会总结转化为论文写作要点。

## 暂存事项

- 如果原始数据集或模型 checkpoint 超出 Git/Git LFS 的适用范围，再加入 DVC。
- 研究总控台和任务看板稳定后，再添加研究专用 Codex skill。
- 为文献笔记加入 Zotero citation-key 工作流。
