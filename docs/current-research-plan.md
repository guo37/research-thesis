# 当前研究主线

最后更新：2026-07-01

## 题目方向

> 面向教育图文问答的模态证据对齐检索与鲁棒推理方法研究

英文工作题目：

> Modality-aware Evidence Alignment Retrieval and Robust Reasoning for Educational Multimodal Question Answering

## 核心问题

教育图文问答不是普通视觉问答，也不是泛化教育资源推荐。它的关键在于：模型是否能找到支持解题的教育证据，判断是否需要视觉模态，并基于可追溯证据给出答案和解释。

本文围绕三个问题展开：

| 问题 | 研究内容 | 核心输出 |
| --- | --- | --- |
| 证据是否对齐？ | RC1：教育图文证据对齐检索 | question-evidence alignment score |
| 图像是否必要？ | RC2：模态必要性判断与鲁棒推理 | modality necessity / reliability score |
| 推理是否有据？ | RC3：证据约束的可解释教育推理 | grounded answer and rationale |

## RC1：教育图文证据对齐检索

目标：给定一道教育题目，检索真正支持解题的文本证据、图像证据或图文组合证据。

重点不是只做资源检索，而是做 evidence alignment：

- question 与 lecture / textbook paragraph 的文本证据对齐；
- question 与 image / diagram 的视觉证据对齐；
- question、answer、skill / topic 与证据之间的教学目标对齐；
- 用 hard negatives 测试模型是否只是语义相似，还是确实对齐了解题证据。

最小实验：

- BM25 / TF-IDF 文本检索；
- Sentence-BERT 文本检索；
- CLIP / SigLIP 图文检索；
- 同 topic / 同 skill 的 hard negative；
- wrong-image hard negative。

指标：

- Recall@1/5/10；
- MRR；
- evidence recall；
- hard-negative error rate；
- wrong-image confusion rate。

## RC2：模态必要性判断与鲁棒推理

目标：判断一道题解题时是否需要图像，以及图像缺失、错误或冗余时模型是否仍然可靠。

标签或伪标签类型：

- `text_sufficient`：文本足够；
- `image_required`：必须使用图像或图示；
- `text_image_complementary`：文本和图像互补；
- `image_irrelevant_or_distracting`：图像无关或会干扰。

当前 ScienceQA 的 Exp0/Exp0.1/Exp0.2 可以保留为 RC2 的 pilot：它已经证明图像存在与 topic / skill 强相关，也证明“缺图不等于需要补图”。

后续主实验应从缺图诊断升级为：

- text-only；
- image-only；
- text + image；
- text + wrong image；
- drop-image；
- retrieved evidence。

指标：

- answer accuracy；
- modality necessity accuracy；
- robustness drop；
- recovery gain；
- false visual reliance rate。

## RC3：证据约束的可解释教育推理

目标：模型不仅输出答案，还要说明使用了哪些证据，并保证解释能被证据支持。

输出格式应保持结构化：

```json
{
  "answer": "...",
  "used_modalities": ["text", "image"],
  "supporting_text": "...",
  "supporting_image_ref": "...",
  "topic": "...",
  "skill": "...",
  "rationale": "..."
}
```

重点不是自由生成长解释，而是 evidence-grounded rationale。

指标：

- answer accuracy；
- evidence grounding rate；
- unsupported claim rate；
- modality grounding accuracy；
- rationale faithfulness。

## 数据集

主线固定为三个教育多模态数据集：

| 数据集 | 角色 | 使用方式 | 当前状态 |
| --- | --- | --- | --- |
| ScienceQA | 起步数据集和 pilot | 科学题目、图像、lecture、solution、topic、skill | 本地已处理 |
| TQA / CK12 | 教材图文问答验证 | 教材文本、图示、问题、答案 | 已生成 HF 流式 schema 样例 |
| AI2D | 科学图示推理验证 | diagram、问题、答案、图示结构 | 已生成 HF 流式 schema 样例 |

## 当前结论

当前已经完成的是 ScienceQA 上的 RC2 pilot，而不是完整论文方法。

已完成：

- ScienceQA 统一资源表；
- 图像存在性结构化诊断；
- 缺图类型候选标注；
- `structural_absence` vs `accidental_missing` 门控；
- 全量缺图样本伪标签排序清单。
- 三数据集统一 schema 样例；
- TQA / CK12 和 AI2D 的 HF 流式样例接入。
- RC1 文本证据对齐检索 baseline。
- RC1 same-topic / same-skill hard negative 评测。
- AI2D wrong-image 候选表。
- AI2D 本地图像缓存与 CLIP / SigLIP 图像证据检索 baseline。
- RC1 结果审计与消融，确认当前仍属于 baseline / evaluation audit。

尚未完成：

- RC1 evidence alignment scorer 训练；
- RC2 的 text/image/wrong-image 鲁棒推理实验；
- RC3 证据约束解释评测集。

## 下一步

优先级：

1. 将 RC1 主实验切换为 no-solution evidence 和 diagram-level 图像评测。
2. 构造固定负样本数的 RC1 训练集和评测集。
3. 训练 evidence alignment scorer。
4. 再用 wrong-image 和 drop-image 构造 RC2 主实验。
