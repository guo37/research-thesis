# Exp0.1 人工标签分析

基于 `data/scienceqa/annotation/missing_type_annotation_candidates.csv` 生成。

## 数据质量

| 检查项 | 值 |
| --- | --- |
| 总行数 | 372 |
| 缺图样本数 | 322 |
| 空白 `human_label` | 0 |
| 非法标签 | 0 |
| 图像状态/标签一致性问题 | 0 |

## 标签分布

| 标签 | 数量 | 占全部样本比例 |
| --- | --- | --- |
| observed | 50 | 13.4% |
| structural_absence | 230 | 61.8% |
| accidental_missing | 92 | 24.7% |
| ambiguous | 0 | 0.0% |

只看缺图样本：

| 标签 | 数量 | 占缺图样本比例 |
| --- | --- | --- |
| structural_absence | 230 | 71.4% |
| accidental_missing | 92 | 28.6% |
| ambiguous | 0 | 0.0% |

## 抽样提示类型 vs 人工标签

| 抽样提示类型 | 总数 | observed | structural_absence | accidental_missing | ambiguous |
| --- | --- | --- | --- | --- | --- |
| structural_absence_candidate | 150 | 0 | 150 | 0 | 0 |
| ambiguous_missing_candidate | 100 | 0 | 8 | 92 | 0 |
| accidental_missing_candidate | 72 | 0 | 72 | 0 | 0 |
| observed_reference | 50 | 50 | 0 | 0 | 0 |

## Subject vs 人工标签

| Subject | 总数 | observed | structural_absence | accidental_missing | ambiguous |
| --- | --- | --- | --- | --- | --- |
| natural science | 204 | 30 | 83 | 91 | 0 |
| social science | 92 | 17 | 74 | 1 | 0 |
| language science | 76 | 3 | 73 | 0 | 0 |

## 数据划分 vs 人工标签

| 数据划分 | 总数 | observed | structural_absence | accidental_missing | ambiguous |
| --- | --- | --- | --- | --- | --- |
| train | 223 | 33 | 137 | 53 | 0 |
| validation | 84 | 10 | 52 | 22 | 0 |
| test | 65 | 7 | 41 | 17 | 0 |

## 主要 Topic

| Topic | 总数 | observed | structural_absence | accidental_missing | ambiguous |
| --- | --- | --- | --- | --- | --- |
| biology | 138 | 10 | 38 | 90 | 0 |
| us-history | 45 | 2 | 43 | 0 | 0 |
| geography | 26 | 14 | 12 | 0 | 0 |
| figurative-language | 22 | 0 | 22 | 0 | 0 |
| physics | 22 | 8 | 14 | 0 | 0 |
| writing-strategies | 19 | 1 | 18 | 0 | 0 |
| chemistry | 15 | 3 | 11 | 1 | 0 |
| reference-skills | 13 | 0 | 13 | 0 | 0 |
| world-history | 12 | 0 | 12 | 0 | 0 |
| units-and-measurement | 11 | 0 | 11 | 0 | 0 |
| earth-science | 8 | 4 | 4 | 0 | 0 |
| punctuation | 8 | 0 | 8 | 0 | 0 |
| economics | 7 | 1 | 5 | 1 | 0 |
| literacy-in-science | 5 | 0 | 5 | 0 | 0 |
| science-and-engineering-practices | 5 | 5 | 0 | 0 | 0 |

## 置信度分布

| 置信度区间 | 数量 |
| --- | --- |
| >=0.90 | 215 |
| 0.80-0.89 | 149 |
| 0.70-0.79 | 8 |
| <0.70 | 0 |
| <blank> | 0 |
| invalid | 0 |

## 结果解读

- 在缺图样本中，`230` / `322`（71.4%）被标为 `structural_absence`。
- 在缺图样本中，`92` / `322`（28.6%）被标为 `accidental_missing`：这些题目需要图，但数据中缺图。
- 人工复核后，没有样本继续保留为 `ambiguous`。
- 下一步 RC2 任务应是二分类模态必要性门控：在缺图样本中预测 `structural_absence` vs `accidental_missing`。
- 正类样本集中在 natural-science/biology，因此论文使用前应进行 topic/skill 分组测试。

## 推荐下一步实验

在缺图样本中，将正类定义为 `accidental_missing`。

运行 Exp0.2 基线对比：

1. 多数类基线。
2. 仅元数据 Logistic Regression：subject、topic、skill、grade、text length。
3. 仅文本 TF-IDF Logistic Regression：question、choices、hint、lecture、solution。
4. 元数据 + 文本 TF-IDF Logistic Regression。

报告 balanced accuracy、macro F1、正类 F1、PR-AUC 和混淆矩阵。

如果 Exp0.2 能明显优于基线地识别“需要图但缺图”的样本，RC2 可以继续按 `MNAR-aware selective completion` 推进。否则，RC2 应收窄为描述性 MNAR 诊断和规则辅助的模态必要性分析。
