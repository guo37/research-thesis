# 实验运行记录

## 元数据

- 日期：2026-07-01
- 实验：Exp1.4 RC1 审计与消融
- 分支：main
- 提交：当前工作区未提交
- 设备：Mac / Codex desktop
- 环境：Codex bundled Python

## 研究问题

在进入 RC2 之前，复查 RC1 的文本检索、hard negative 和图像检索结果是否受到答案泄漏、字段选择、候选池大小或重复图像影响。

## 配置

- 配置文件：`configs/exp1_4_rc1_audit.yaml`
- 数据集：ScienceQA / TQA-CK12 / AI2D schema samples
- 输入路径：`data/educational_mm/schema_samples/`
- 输出路径：`reports/exp1_4_rc1_audit/`

## 命令

```bash
/Users/xcs/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/exp1_4_rc1_audit.py --config configs/exp1_4_rc1_audit.yaml
```

## 结果

- ScienceQA full evidence 的正确选项泄漏率：0.7323。
- ScienceQA 去掉 `solution` 后，TF-IDF Recall@1 从 0.8889 降到 0.7041。
- ScienceQA no-solution 下，`question_only` Recall@1 = 0.5799，加入 choices 后为 0.6036，再加入 topic/skill 后为 0.7041。
- 等大小候选池审计中，same-skill hard negative 比 random 更难，但不是训练提升。
- AI2D 200 个样本只有 86 个唯一 diagram hash；167 张图落在重复图组中。
- CLIP lexical wrong-image confusion 去除 same-diagram pair 后从 0.4420 降到 0.2470。

## 解读

RC1 当前结果必须降级表述为 baseline 和评测审计，不能表述为训练后的方法提升。后续 RC1 主实验应使用 no-solution evidence、diagram-level 图像评测、固定负样本数的 hard-negative 训练/评测。

## 下一步

在干净评测定义上训练一个 evidence alignment scorer，再进入 RC2。
