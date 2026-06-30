# Exp0 数据集统计

## 1. ScienceQA 基本规模

- 总样本数：16
- 总体 has_image 比例：0.5000
- 总体缺失比例：0.5000

## 2. Train / Validation / Test 样本数

| split      | n |
| ---------- | - |
| train      | 8 |
| validation | 4 |
| test       | 4 |

## 3. 图像可用性分布

| has_image | n | rate   |
| --------- | - | ------ |
| 1         | 8 | 0.5000 |
| 0         | 8 | 0.5000 |

## 4. Subject / Topic / Skill 分布

| field    | unique_values | non_empty |
| -------- | ------------- | --------- |
| subject  | 2             | 16        |
| topic    | 13            | 16        |
| skill    | 16            | 16        |
| grade    | 3             | 16        |
| category | 10            | 16        |

## 5. Subject 层面的图像缺失率

| subject          | n | has_image_count | has_image_rate | missing_count | missing_rate |
| ---------------- | - | --------------- | -------------- | ------------- | ------------ |
| language science | 7 | 0               | 0.0000         | 7             | 1.0000       |
| natural science  | 9 | 8               | 0.8889         | 1             | 0.1111       |

## 6. Topic 层面的图像缺失率

主要 topic 阈值：`topic_count >= 20`。

_无记录。_

## 7. Skill 层面的图像缺失率

主要 skill 阈值：`skill_count >= 20`。

_无记录。_

## 8. 互信息

| field   | mutual_information |
| ------- | ------------------ |
| subject | 0.9939             |
| topic   | 0.7469             |
| skill   | 0.7265             |
| grade   | 0.5753             |

## 9. 卡方检验

| field   | chi2    | p_value | dof     |
| ------- | ------- | ------- | ------- |
| subject | 9.1429  | 0.0025  | 1.0000  |
| topic   | 16.0000 | 0.1912  | 12.0000 |
| skill   | 16.0000 | 0.3821  | 15.0000 |
| grade   | 9.5000  | 0.0087  | 2.0000  |

## 10. 缺失预测 AUC

| model               | eval_split | auc    | average_precision | f1     | accuracy | positive_rate | features                                         |
| ------------------- | ---------- | ------ | ----------------- | ------ | -------- | ------------- | ------------------------------------------------ |
| majority            | validation | 0.5000 | 0.5000            | 0.0000 | 0.5000   | 0.5000        | subject                                          |
| majority            | test       | 0.5000 | 0.5000            | 0.0000 | 0.5000   | 0.5000        | subject                                          |
| subject_only        | validation | 1.0000 | 1.0000            | 1.0000 | 1.0000   | 0.5000        | subject                                          |
| subject_only        | test       | 1.0000 | 1.0000            | 1.0000 | 1.0000   | 0.5000        | subject                                          |
| topic_only          | validation | 0.5000 | 0.5000            | 0.0000 | 0.5000   | 0.5000        | topic                                            |
| topic_only          | test       | 0.8750 | 0.8333            | 0.6667 | 0.7500   | 0.5000        | topic                                            |
| skill_only          | validation | 0.5000 | 0.5000            | 0.6667 | 0.5000   | 0.5000        | skill                                            |
| skill_only          | test       | 0.5000 | 0.5000            | 0.6667 | 0.5000   | 0.5000        | skill                                            |
| topic_skill         | validation | 0.5000 | 0.5000            | 0.0000 | 0.5000   | 0.5000        | topic,skill                                      |
| topic_skill         | test       | 0.8750 | 0.8333            | 0.6667 | 0.7500   | 0.5000        | topic,skill                                      |
| subject_topic_skill | validation | 1.0000 | 1.0000            | 1.0000 | 1.0000   | 0.5000        | subject,topic,skill                              |
| subject_topic_skill | test       | 1.0000 | 1.0000            | 1.0000 | 1.0000   | 0.5000        | subject,topic,skill                              |
| full_metadata_text  | validation | 1.0000 | 1.0000            | 1.0000 | 1.0000   | 0.5000        | subject,topic,skill,grade,text_length,word_count |
| full_metadata_text  | test       | 1.0000 | 1.0000            | 0.6667 | 0.7500   | 0.5000        | subject,topic,skill,grade,text_length,word_count |

## 11. High-MNAR / Low-MNAR Topic 候选

High-MNAR 候选是高频且缺失率高的 topic；Low-MNAR 候选是高频且缺失率低的 topic。

### High-MNAR Topic 候选

_无记录。_

### Low-MNAR Topic 候选

_无记录。_

## 12. RC2 后续判断

结构性缺失信号较弱或不明确：完整元数据模型没有明显优于 subject-only。

注意：Exp0 不能把缺图直接等同于 `structural_absence`。缺失类型必须通过后续 300-500 条样本标注确认。
