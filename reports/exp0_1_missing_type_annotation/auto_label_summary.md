# Exp0.1 自动预标注汇总

生成日期：2026-06-30

> 已被人工复核覆盖：91 条自动预标为 `ambiguous` 的样本已经复核，并因“需要图但 `has_image=0`”被重标为 `accidental_missing`。当前标签证据以 `human_label_analysis.md` 为准。

## 方法

一次保守的规则辅助模型处理填充了 `data/scienceqa/annotation/missing_type_annotation_candidates.csv` 中的 `human_label`、`label_confidence` 和 `label_note`。中间自动预标注副本保留在 `data/scienceqa/annotation/missing_type_annotation_candidates_auto_labeled.csv`，用于审计。

判定策略：

- `observed`: `has_image=1`.
- `accidental_missing`：存在明确视觉/材料线索，但 `has_image=0`。
- `structural_absence`：题目和选项以文本形式已经足够，没有明确视觉依赖。
- `ambiguous`：视觉支持可能相关，或仅凭文本无法有把握地判断缺失类型。

这些是预标注，不是最终裁定标签。使用分布作为论文证据前，需要复核低置信行。

## 标签分布

| Label | Count |
| --- | ---: |
| observed | 50 |
| structural_absence | 230 |
| accidental_missing | 1 |
| ambiguous | 91 |

## 置信度分布

| 置信度区间 | 数量 |
| --- | ---: |
| >=0.90 | 124 |
| 0.80-0.89 | 149 |
| 0.70-0.79 | 8 |
| <0.70 | 91 |

## 原始抽样提示

| 抽样提示类型 | 数量 |
| --- | ---: |
| structural_absence_candidate | 150 |
| ambiguous_missing_candidate | 100 |
| accidental_missing_candidate | 72 |
| observed_reference | 50 |

## 复核队列

需要复核的行已写入 `reports/exp0_1_missing_type_annotation/auto_label_review_queue.csv`。

推荐复核优先级：

1. 所有 `accidental_missing` 行。
2. 所有 `ambiguous` 行。
3. 所有置信度低于 0.80 的行。
4. 从 `structural_absence` 行中随机抽样，尤其关注 natural-science 分类题。

