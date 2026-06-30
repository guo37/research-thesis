# Exp0.2 选择性补全门控基线

目标：

```text
0 = structural_absence
1 = image_needed_missing = accidental_missing
```

## 数据

- 使用样本：322 条已标注缺图候选样本。
- 标签计数：`{"accidental_missing": 92, "structural_absence": 230}`。
- 目标计数：`{"0": 230, "1": 92}`。

## 指标

| model | split | threshold | n | positive_rate | balanced_accuracy | macro_f1 | positive_f1 | positive_precision | positive_recall | pr_auc | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| majority | validation |  | 74 | 0.2973 | 0.5000 | 0.4127 | 0.0000 | 0.0000 | 0.0000 | 0.2973 | 52 | 0 | 22 | 0 |
| majority | test |  | 58 | 0.2931 | 0.5000 | 0.4141 | 0.0000 | 0.0000 | 0.0000 | 0.2931 | 41 | 0 | 17 | 0 |
| metadata | validation | 0.5000 | 74 | 0.2973 | 0.9808 | 0.9685 | 0.9565 | 0.9167 | 1.0000 | 0.9941 | 50 | 2 | 0 | 22 |
| metadata | test | 0.5000 | 58 | 0.2931 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 41 | 0 | 0 | 17 |
| text | validation | 0.3500 | 74 | 0.2973 | 0.9808 | 0.9685 | 0.9565 | 0.9167 | 1.0000 | 0.9878 | 50 | 2 | 0 | 22 |
| text | test | 0.3500 | 58 | 0.2931 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 41 | 0 | 0 | 17 |
| metadata_text | validation | 0.3500 | 74 | 0.2973 | 0.9808 | 0.9685 | 0.9565 | 0.9167 | 1.0000 | 0.9941 | 50 | 2 | 0 | 22 |
| metadata_text | test | 0.3500 | 58 | 0.2931 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 41 | 0 | 0 | 17 |

## 划分重叠检查

| 字段 | 数据划分 | 唯一值数量 | 训练集中未见值数量 | 示例 |
| --- | --- | --- | --- | --- |
| topic | validation | 16 | 0 |  |
| topic | test | 16 | 1 | reading-comprehension |
| skill | validation | 50 | 21 | Antebellum Period: economies of the North and South, Changes to Earth's surface: earthquakes, Changes to Earth's surface: erosion, Choose metric units of mass, Classify changes to Earth's surface |
| skill | test | 39 | 16 | Banks, Benjamin Franklin, Choose customary units of volume, Formatting titles, Identify elementary substances and compounds using chemical formulas |

如果验证集/测试集中的 topic 或 skill 大多已经出现在训练集中，高分可能部分来自 topic/skill 记忆效应。作为论文证据前，需要增加分组压力测试。

## 当前最佳测试结果

- 按正类 F1 选择的最佳模型：`metadata`。
- 正类 F1：`1.0000`。
- PR-AUC：`1.0000`。
- Balanced accuracy：`1.0000`。
- 测试集混淆矩阵：TN=41, FP=0, FN=0, TP=17。

## 结果解读

- 当前标注集较小，因此该结果是可行性信号，还不是最终论文证据。
- 结果支持将 RC2 表述为模态必要性门控：跳过结构性无图，处理意外缺图。
- 如果标签包含自动辅助过程，在写入论文前应抽查正类样本。
