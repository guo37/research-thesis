# 实验运行记录

## 元数据

- 日期：2026-07-01
- 实验：Exp1.2 hard negative 与 wrong-image 候选构造
- 分支：main
- 提交：当前工作区未提交
- 设备：Mac / Codex desktop
- 环境：Codex bundled Python；本环境缺少 PyYAML，脚本使用内置默认配置

## 研究问题

RC1 文本证据检索在同 topic / 同 skill hard negative 候选池中是否仍能稳定命中正确证据？AI2D 是否可以先构造 wrong-image 候选，为后续 CLIP / SigLIP 图像检索和 RC2 wrong-image 实验提供输入？

## 配置

- 配置文件：`configs/exp1_2_hard_negative_retrieval.yaml`
- 数据集：ScienceQA schema sample、TQA / CK12 schema sample、AI2D schema sample
- 输入路径：`data/educational_mm/schema_samples/`
- 输出路径：`reports/exp1_2_hard_negative_retrieval/`

## 命令

```bash
/Users/xcs/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/exp1_2_hard_negative_retrieval.py --config configs/exp1_2_hard_negative_retrieval.yaml
```

## 结果

- ScienceQA TF-IDF random Recall@1：0.9899。
- ScienceQA TF-IDF same-topic Recall@1：0.9031。
- ScienceQA TF-IDF same-skill Recall@1：0.8954。
- AI2D wrong-image 候选对：4,000。

## 解读

同 topic / 同 skill 候选池明显比 random 候选池更难，能暴露 ScienceQA 中相近教学目标证据之间的混淆。TQA / CK12 的唯一文本证据只有 9 条，当前结果只能说明流程打通，不能代表完整教材证据检索表现。AI2D 目前只有 `hf://` 图像引用，因此本次只构造 wrong-image 候选，不声称已完成图像向量检索。

## 下一步

补齐 AI2D / TQA 本地图像文件或缓存，并在 wrong-image 候选表上运行 CLIP / SigLIP 图文证据检索 baseline。
