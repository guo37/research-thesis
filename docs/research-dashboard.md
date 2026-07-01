# 研究总控台

最后更新：2026-07-01

这是毕业论文研究工作空间的工作入口。打开实验文件、论文草稿或组会记录前，先从这里开始。

## 当前论文主线

题目方向：

> 面向教育图文问答的模态证据对齐检索与鲁棒推理方法研究

核心主线：

> 教育图文证据对齐检索 + 模态必要性判断与鲁棒推理 + 证据约束的可解释教育推理。

规范规划文件：

- [current-research-plan.md](current-research-plan.md)

## 当前工作流

| 工作流 | 状态 | 下一步 |
| --- | --- | --- |
| 统一数据 schema | ScienceQA / TQA / AI2D 样例已完成 | 作为后续实验统一输入 |
| RC1 证据对齐检索 | baseline、hard negative、AI2D 图像检索、Exp1.4 审计和 Exp1.5 clean benchmark 已完成 | 训练 evidence alignment scorer，并扩展 clean benchmark 样本规模 |
| RC2 模态必要性判断 | ScienceQA pilot 已完成 | 等 RC1 clean scorer 稳定后升级为 text/image/wrong-image 鲁棒推理实验 |
| RC3 证据约束解释 | 计划中 | 在 RC1/RC2 输入稳定后构建 100 条解释评测集 |
| 文献综述 | 进行中 | 围绕教育图文问答、证据检索、模态鲁棒性、忠实解释扩展 |
| 组会汇报 | 需要规范化 | 使用两周组会节奏和 PPT 模板 |

## 核心索引

- [任务看板](task-board.md)
- [实验登记表](experiment-registry.md)
- [论文路线图](paper-roadmap.md)
- [当前研究主线](current-research-plan.md)
- [结果输出前审查协议](result-review-protocol.md)
- [组会周期](meeting-cycle.md)
- [研究空间地图](research-space-map.md)
- [多设备同步](multi-device-sync.md)

## 每次工作流程

1. Run `scripts/sync_start.ps1` or `scripts/sync_start.sh`.
2. 查看 [任务看板](task-board.md)。
3. 一次只处理一个活动任务。
4. 按 [结果输出前审查协议](result-review-protocol.md) 复查指标来源。
5. 记录实验命令、输出、结果解读和迭代动作。
6. 切换设备前运行 `scripts/sync_finish.ps1` 或 `scripts/sync_finish.sh`。

## 证据规则

- 关于统一 schema 的结论必须引用数据字段覆盖率和样例表。
- 关于 RC1 的结论必须引用检索指标和 hard negative 基线对比。
- 关于 RC2 的结论必须引用模态必要性、wrong-image、drop-image 实验。
- 关于 RC3 的结论必须引用解释样本、证据 grounding 和 unsupported claim 评测。
- 论文草稿必须区分已经验证的结果和工作性假设。

## 当前 ScienceQA Pilot 判断

Exp0/Exp0.1/Exp0.2 当前支持把 ScienceQA 作为 RC2 pilot：

- 候选集中多数缺图样本被标为 `structural_absence`。
- 人工复核表明，原先的 `ambiguous` 行属于“需要图但缺图”的样本。
- 当前缺图候选集包含 230 条 `structural_absence` 和 92 条 `accidental_missing`。
- Exp0.2 表明二分类门控在原始划分和 `skill_holdout` 上有可行性信号。
- 这部分不再作为完整论文主线，而是服务于“模态必要性判断”的前置证据。
