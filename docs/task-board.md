# 研究任务看板

最后更新：2026-06-30

这个文件只维护短期操作队列。复杂推理应写入对应实验、论文或组会文件。

## 当前

- [x] 将最新主线调整为“教育图文证据对齐检索 + 模态必要性判断 + 证据约束推理”。
- [x] 归档旧“教育资源检索可信多模态知识推理”路线文档。
- [x] 删除 Exp0 smoke 旧报告，保留正式 Exp0/Exp0.1/Exp0.2 证据链。
- [x] 完成 Exp1.0：ScienceQA 统一 schema 样例。
- [x] 接入 TQA / CK12，并抽取 200 条统一 schema 样例。
- [x] 接入 AI2D，并抽取 200 条统一 schema 样例。
- [x] 定义并实现 RC1 文本证据对齐检索 baseline。
- [ ] 为 RC1 增加 same-topic / same-skill hard negative 评测。
- [ ] 为 AI2D 增加图像/diagram 证据检索 baseline。
- [ ] 设计 RC2 的 text-only / text+image / wrong-image / drop-image 实验。
- [ ] 定义 RC3 的 100 条证据约束解释评测集 schema。

## 下一步

- [ ] 设计 RC1 hard negative：same-topic、same-skill、wrong-image。
- [ ] 扩展到 Sentence-BERT 文本检索 baseline。
- [ ] 实现 CLIP / SigLIP 图文证据检索 baseline。
- [ ] 记录 TQA 官方完整包接入方案，用于后续补齐原始 diagram 文件。
- [ ] 将文献综述按新主线重排为：教育图文问答、证据检索、模态鲁棒性、忠实解释。

## 后续

- [ ] 增加 RC1 证据对齐检索实验脚本和配置。
- [ ] 增加 RC2 模态必要性判断和鲁棒推理实验脚本。
- [ ] 增加 RC3 证据约束解释生成脚本和评测报告。
- [ ] 将稳定的组会总结转化为论文写作要点。

## 暂存事项

- 如果原始数据集或模型 checkpoint 超出 Git/Git LFS 的适用范围，再加入 DVC。
- 研究总控台和任务看板稳定后，再添加研究专用 Codex skill。
- 为文献笔记加入 Zotero citation-key 工作流。
