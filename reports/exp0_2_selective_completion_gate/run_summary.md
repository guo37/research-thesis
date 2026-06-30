# Exp0.2 选择性补全门控基线

目标：

```text
0 = structural_absence
1 = image_needed_missing = accidental_missing
```

## 数据

- ScienceQA 全量样本：21,208 条。
- ScienceQA 缺图样本：10,876 条。
- 当前有真值标签的缺图样本：322 条。
- 标签计数：`{"accidental_missing": 92, "structural_absence": 230}`。
- 目标计数：`{"0": 230, "1": 92}`。

## 评测设计

- `original_split`：沿用 ScienceQA 原始 train / validation / test 样本划分，测试模型是否见过同一条样本。
- `topic_holdout`：按 topic 分组划分，validation / test 的 topic 不出现在训练集中。
- `skill_holdout`：按 skill 分组划分，validation / test 的 skill 不出现在训练集中。

## 分组划分诊断

| scenario       | holdout_field | split      | n   | positive | negative | positive_rate | group_count | unseen_group_count | examples                                                                                                                                         |
| -------------- | ------------- | ---------- | --- | -------- | -------- | ------------- | ----------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| original_split | sample_id     | train      | 190 | 53       | 137      | 0.2789        | 190         | 0                  |                                                                                                                                                  |
| original_split | sample_id     | validation | 74  | 22       | 52       | 0.2973        | 74          | 74                 |                                                                                                                                                  |
| original_split | sample_id     | test       | 58  | 17       | 41       | 0.2931        | 58          | 58                 |                                                                                                                                                  |
| topic_holdout  | topic         | train      | 192 | 90       | 102      | 0.4688        | 5           | 0                  |                                                                                                                                                  |
| topic_holdout  | topic         | validation | 66  | 1        | 65       | 0.0152        | 9           | 9                  | chemistry, civics, physics, punctuation, reading-comprehension                                                                                   |
| topic_holdout  | topic         | test       | 64  | 1        | 63       | 0.0156        | 6           | 6                  | earth-science, economics, figurative-language, phonological-awareness, world-history                                                             |
| skill_holdout  | skill         | train      | 194 | 56       | 138      | 0.2887        | 65          | 0                  |                                                                                                                                                  |
| skill_holdout  | skill         | validation | 64  | 19       | 45       | 0.2969        | 30          | 30                 | Abraham Lincoln, Benjamin Franklin, Body systems: perception and motion, Cesar Chavez, Choose customary units of distance, mass, and volume      |
| skill_holdout  | skill         | test       | 64  | 17       | 47       | 0.2656        | 41          | 41                 | Antebellum Period: abolitionist and proslavery perspectives, Banks, Bill Gates, Body systems: digestion, Changes to Earth's surface: earthquakes |

## 测试集最佳结果

| scenario       | model    | n   | positive_f1 | balanced_accuracy | macro_f1 | pr_auc | tn  | fp  | fn  | tp  |
| -------------- | -------- | --- | ----------- | ----------------- | -------- | ------ | --- | --- | --- | --- |
| original_split | metadata | 58  | 1.0000      | 1.0000            | 1.0000   | 1.0000 | 41  | 0   | 0   | 17  |
| skill_holdout  | text     | 64  | 0.8000      | 0.8692            | 0.8624   | 0.8553 | 43  | 4   | 3   | 14  |
| topic_holdout  | majority | 64  | 0.0000      | 0.5000            | 0.4961   | 0.0156 | 63  | 0   | 1   | 0   |

## 全部指标

| scenario       | model         | split      | threshold | n   | positive_rate | balanced_accuracy | macro_f1 | positive_f1 | positive_precision | positive_recall | pr_auc | tn  | fp  | fn  | tp  |
| -------------- | ------------- | ---------- | --------- | --- | ------------- | ----------------- | -------- | ----------- | ------------------ | --------------- | ------ | --- | --- | --- | --- |
| original_split | majority      | validation |           | 74  | 0.2973        | 0.5000            | 0.4127   | 0.0000      | 0.0000             | 0.0000          | 0.2973 | 52  | 0   | 22  | 0   |
| original_split | majority      | test       |           | 58  | 0.2931        | 0.5000            | 0.4141   | 0.0000      | 0.0000             | 0.0000          | 0.2931 | 41  | 0   | 17  | 0   |
| original_split | metadata      | validation | 0.5000    | 74  | 0.2973        | 0.9808            | 0.9685   | 0.9565      | 0.9167             | 1.0000          | 0.9941 | 50  | 2   | 0   | 22  |
| original_split | metadata      | test       | 0.5000    | 58  | 0.2931        | 1.0000            | 1.0000   | 1.0000      | 1.0000             | 1.0000          | 1.0000 | 41  | 0   | 0   | 17  |
| original_split | text          | validation | 0.3500    | 74  | 0.2973        | 0.9808            | 0.9685   | 0.9565      | 0.9167             | 1.0000          | 0.9878 | 50  | 2   | 0   | 22  |
| original_split | text          | test       | 0.3500    | 58  | 0.2931        | 1.0000            | 1.0000   | 1.0000      | 1.0000             | 1.0000          | 1.0000 | 41  | 0   | 0   | 17  |
| original_split | metadata_text | validation | 0.3500    | 74  | 0.2973        | 0.9808            | 0.9685   | 0.9565      | 0.9167             | 1.0000          | 0.9941 | 50  | 2   | 0   | 22  |
| original_split | metadata_text | test       | 0.3500    | 58  | 0.2931        | 1.0000            | 1.0000   | 1.0000      | 1.0000             | 1.0000          | 1.0000 | 41  | 0   | 0   | 17  |
| topic_holdout  | majority      | validation |           | 66  | 0.0152        | 0.5000            | 0.4962   | 0.0000      | 0.0000             | 0.0000          | 0.0152 | 65  | 0   | 1   | 0   |
| topic_holdout  | majority      | test       |           | 64  | 0.0156        | 0.5000            | 0.4961   | 0.0000      | 0.0000             | 0.0000          | 0.0156 | 63  | 0   | 1   | 0   |
| topic_holdout  | metadata      | validation | 0.2000    | 66  | 0.0152        | 0.9231            | 0.5417   | 0.1667      | 0.0909             | 1.0000          | 0.1000 | 55  | 10  | 0   | 1   |
| topic_holdout  | metadata      | test       | 0.2000    | 64  | 0.0156        | 0.4921            | 0.4921   | 0.0000      | 0.0000             | 0.0000          | 0.0192 | 62  | 1   | 1   | 0   |
| topic_holdout  | text          | validation | 0.5500    | 66  | 0.0152        | 1.0000            | 1.0000   | 1.0000      | 1.0000             | 1.0000          | 1.0000 | 65  | 0   | 0   | 1   |
| topic_holdout  | text          | test       | 0.5500    | 64  | 0.0156        | 0.5000            | 0.4961   | 0.0000      | 0.0000             | 0.0000          | 0.5000 | 63  | 0   | 1   | 0   |
| topic_holdout  | metadata_text | validation | 0.2500    | 66  | 0.0152        | 0.9308            | 0.5537   | 0.1818      | 0.1000             | 1.0000          | 0.1000 | 56  | 9   | 0   | 1   |
| topic_holdout  | metadata_text | test       | 0.2500    | 64  | 0.0156        | 0.4921            | 0.4921   | 0.0000      | 0.0000             | 0.0000          | 0.0196 | 62  | 1   | 1   | 0   |
| skill_holdout  | majority      | validation |           | 64  | 0.2969        | 0.5000            | 0.4128   | 0.0000      | 0.0000             | 0.0000          | 0.2969 | 45  | 0   | 19  | 0   |
| skill_holdout  | majority      | test       |           | 64  | 0.2656        | 0.5000            | 0.4234   | 0.0000      | 0.0000             | 0.0000          | 0.2656 | 47  | 0   | 17  | 0   |
| skill_holdout  | metadata      | validation | 0.2000    | 64  | 0.2969        | 0.8544            | 0.8385   | 0.7805      | 0.7273             | 0.8421          | 0.7317 | 39  | 6   | 3   | 16  |
| skill_holdout  | metadata      | test       | 0.2000    | 64  | 0.2656        | 0.6020            | 0.6082   | 0.4000      | 0.4615             | 0.3529          | 0.4101 | 40  | 7   | 11  | 6   |
| skill_holdout  | text          | validation | 0.2500    | 64  | 0.2969        | 0.8433            | 0.8228   | 0.7619      | 0.6957             | 0.8421          | 0.7660 | 38  | 7   | 3   | 16  |
| skill_holdout  | text          | test       | 0.2500    | 64  | 0.2656        | 0.8692            | 0.8624   | 0.8000      | 0.7778             | 0.8235          | 0.8553 | 43  | 4   | 3   | 14  |
| skill_holdout  | metadata_text | validation | 0.1500    | 64  | 0.2969        | 0.8807            | 0.8583   | 0.8095      | 0.7391             | 0.8947          | 0.7438 | 39  | 6   | 2   | 17  |
| skill_holdout  | metadata_text | test       | 0.1500    | 64  | 0.2656        | 0.6101            | 0.6121   | 0.4242      | 0.4375             | 0.4118          | 0.4739 | 38  | 9   | 10  | 7   |

## 全量缺图预测

- 预测模型：`text`。
- 使用阈值：`0.3500`。
- 输出文件：`reports\exp0_2_selective_completion_gate\full_missing_predictions.csv`。
- 人工复核清单：`reports\exp0_2_selective_completion_gate\full_missing_review_candidates.csv`。
- 全量缺图样本：10876 条。
- 其中已有人工标签来源样本：322 条。
- 其余未标注缺图样本：10554 条。
- 全量预测计数：`{"need_completion_accidental_missing": 529, "skip_structural_absence": 10347}`。
- 未标注样本预测计数：`{"need_completion_accidental_missing": 428, "skip_structural_absence": 10126}`。
- 概率分位数：`{"0.1": 0.12394216935779151, "0.25": 0.14689809121110875, "0.5": 0.1730506288178785, "0.75": 0.19915628812176894, "0.9": 0.27146255981641476}`。

## 结果解读

- 372 条候选样本不是全量数据；真正有二分类真值的缺图样本是 322 条。
- 原始划分只能说明模型没有见过同一条样本，不能排除 topic / skill 记忆效应。
- 分组留出结果用于判断模型能否泛化到未见过的 topic 或 skill。
- 全量缺图预测是伪标签和排序清单，不能直接当作准确率；写入论文前应继续抽查高置信正类和高置信负类。
