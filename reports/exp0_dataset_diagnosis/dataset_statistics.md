# Exp0 数据集统计

## 1. ScienceQA 基本规模

- 总样本数：21208
- 总体 has_image 比例：0.4872
- 总体缺失比例：0.5128

## 2. Train / Validation / Test 样本数

| split      | n     |
| ---------- | ----- |
| train      | 12726 |
| validation | 4241  |
| test       | 4241  |

## 3. 图像可用性分布

| has_image | n     | rate   |
| --------- | ----- | ------ |
| 0         | 10876 | 0.5128 |
| 1         | 10332 | 0.4872 |

## 4. Subject / Topic / Skill 分布

| field    | unique_values | non_empty |
| -------- | ------------- | --------- |
| subject  | 3             | 21208     |
| topic    | 26            | 21208     |
| skill    | 379           | 21208     |
| grade    | 12            | 21208     |
| category | 126           | 21208     |

## 5. Subject 层面的图像缺失率

| subject          | n     | has_image_count | has_image_rate | missing_count | missing_rate |
| ---------------- | ----- | --------------- | -------------- | ------------- | ------------ |
| language science | 5371  | 228             | 0.0425         | 5143          | 0.9575       |
| natural science  | 11487 | 6332            | 0.5512         | 5155          | 0.4488       |
| social science   | 4350  | 3772            | 0.8671         | 578           | 0.1329       |

## 6. Topic 层面的图像缺失率

主要 topic 阈值：`topic_count >= 20`。

| topic                             | n    | has_image_count | has_image_rate | missing_count | missing_rate |
| --------------------------------- | ---- | --------------- | -------------- | ------------- | ------------ |
| figurative-language               | 1260 | 0               | 0.0000         | 1260          | 1.0000       |
| units-and-measurement             | 870  | 0               | 0.0000         | 870           | 1.0000       |
| reference-skills                  | 724  | 0               | 0.0000         | 724           | 1.0000       |
| punctuation                       | 514  | 0               | 0.0000         | 514           | 1.0000       |
| grammar                           | 379  | 0               | 0.0000         | 379           | 1.0000       |
| verbs                             | 251  | 0               | 0.0000         | 251           | 1.0000       |
| capitalization                    | 198  | 0               | 0.0000         | 198           | 1.0000       |
| phonological-awareness            | 97   | 0               | 0.0000         | 97            | 1.0000       |
| civics                            | 126  | 8               | 0.0635         | 118           | 0.9365       |
| writing-strategies                | 1650 | 139             | 0.0842         | 1511          | 0.9158       |
| vocabulary                        | 162  | 24              | 0.1481         | 138           | 0.8519       |
| economics                         | 682  | 298             | 0.4370         | 384           | 0.5630       |
| chemistry                         | 1194 | 536             | 0.4489         | 658           | 0.5511       |
| word-study                        | 39   | 19              | 0.4872         | 20            | 0.5128       |
| biology                           | 4098 | 2103            | 0.5132         | 1995          | 0.4868       |
| reading-comprehension             | 84   | 46              | 0.5476         | 38            | 0.4524       |
| physics                           | 3215 | 2202            | 0.6849         | 1013          | 0.3151       |
| science-and-engineering-practices | 924  | 635             | 0.6872         | 289           | 0.3128       |
| earth-science                     | 1152 | 827             | 0.7179         | 325           | 0.2821       |
| world-history                     | 65   | 53              | 0.8154         | 12            | 0.1846       |

## 7. Skill 层面的图像缺失率

主要 skill 阈值：`skill_count >= 20`。

| skill                                                                   | n   | has_image_count | has_image_rate | missing_count | missing_rate |
| ----------------------------------------------------------------------- | --- | --------------- | -------------- | ------------- | ------------ |
| Use guide words                                                         | 697 | 0               | 0.0000         | 697           | 1.0000       |
| Inherited and acquired traits: use evidence to support a statement      | 585 | 0               | 0.0000         | 585           | 1.0000       |
| Compare physical and chemical changes                                   | 447 | 0               | 0.0000         | 447           | 1.0000       |
| Classify logical fallacies                                              | 373 | 0               | 0.0000         | 373           | 1.0000       |
| Recall the source of an allusion                                        | 337 | 0               | 0.0000         | 337           | 1.0000       |
| Identify questions that can be investigated with a set of materials     | 289 | 0               | 0.0000         | 289           | 1.0000       |
| Greetings and closings of letters                                       | 288 | 0               | 0.0000         | 288           | 1.0000       |
| Identify inherited and acquired traits                                  | 280 | 0               | 0.0000         | 280           | 1.0000       |
| Identify vague pronoun references                                       | 261 | 0               | 0.0000         | 261           | 1.0000       |
| Interpret figures of speech                                             | 257 | 0               | 0.0000         | 257           | 1.0000       |
| Genetics vocabulary: genotype and phenotype                             | 251 | 0               | 0.0000         | 251           | 1.0000       |
| Is the sentence in the past, present, or future tense?                  | 251 | 0               | 0.0000         | 251           | 1.0000       |
| Explore words with new or contested usages                              | 215 | 0               | 0.0000         | 215           | 1.0000       |
| Genetics vocabulary: dominant and recessive                             | 205 | 0               | 0.0000         | 205           | 1.0000       |
| Is the sentence declarative, interrogative, imperative, or exclamatory? | 202 | 0               | 0.0000         | 202           | 1.0000       |
| Compare the speeds of moving objects                                    | 200 | 0               | 0.0000         | 200           | 1.0000       |
| Costs and benefits                                                      | 197 | 0               | 0.0000         | 197           | 1.0000       |
| How is temperature related to thermal energy?                           | 195 | 0               | 0.0000         | 195           | 1.0000       |
| Compare properties of materials                                         | 151 | 0               | 0.0000         | 151           | 1.0000       |
| What's the difference between weather and climate?                      | 149 | 0               | 0.0000         | 149           | 1.0000       |

## 8. 互信息

| field   | mutual_information |
| ------- | ------------------ |
| subject | 0.2505             |
| topic   | 0.3211             |
| skill   | 0.6884             |
| grade   | 0.0719             |

## 9. 卡方检验

| field   | chi2       | p_value | dof      |
| ------- | ---------- | ------- | -------- |
| subject | 6954.1395  | 0.0000  | 2.0000   |
| topic   | 9745.0370  | 0.0000  | 25.0000  |
| skill   | 20933.3005 | 0.0000  | 378.0000 |
| grade   | 2275.1555  | 0.0000  | 11.0000  |

## 10. 缺失预测 AUC

| model               | eval_split | auc    | average_precision | f1     | accuracy | positive_rate | features                                         |
| ------------------- | ---------- | ------ | ----------------- | ------ | -------- | ------------- | ------------------------------------------------ |
| majority            | validation | 0.5000 | 0.4945            | 0.0000 | 0.5055   | 0.4945        | subject                                          |
| majority            | test       | 0.5000 | 0.4756            | 0.0000 | 0.5244   | 0.4756        | subject                                          |
| subject_only        | validation | 0.7955 | 0.7281            | 0.7718 | 0.7142   | 0.4945        | subject                                          |
| subject_only        | test       | 0.7985 | 0.7124            | 0.7650 | 0.7142   | 0.4756        | subject                                          |
| topic_only          | validation | 0.8693 | 0.8463            | 0.7906 | 0.7649   | 0.4945        | topic                                            |
| topic_only          | test       | 0.8833 | 0.8509            | 0.7951 | 0.7791   | 0.4756        | topic                                            |
| skill_only          | validation | 0.9996 | 0.9995            | 0.9883 | 0.9884   | 0.4945        | skill                                            |
| skill_only          | test       | 0.9997 | 0.9996            | 0.9896 | 0.9901   | 0.4756        | skill                                            |
| topic_skill         | validation | 0.9996 | 0.9995            | 0.9910 | 0.9910   | 0.4945        | topic,skill                                      |
| topic_skill         | test       | 0.9997 | 0.9995            | 0.9909 | 0.9913   | 0.4756        | topic,skill                                      |
| subject_topic_skill | validation | 0.9996 | 0.9995            | 0.9913 | 0.9913   | 0.4945        | subject,topic,skill                              |
| subject_topic_skill | test       | 0.9996 | 0.9994            | 0.9909 | 0.9913   | 0.4756        | subject,topic,skill                              |
| full_metadata_text  | validation | 0.9998 | 0.9998            | 0.9917 | 0.9917   | 0.4945        | subject,topic,skill,grade,text_length,word_count |
| full_metadata_text  | test       | 0.9997 | 0.9996            | 0.9902 | 0.9906   | 0.4756        | subject,topic,skill,grade,text_length,word_count |

## 11. High-MNAR / Low-MNAR Topic 候选

High-MNAR 候选是高频且缺失率高的 topic；Low-MNAR 候选是高频且缺失率低的 topic。

### High-MNAR Topic 候选

| topic                             | n    | has_image_count | has_image_rate | missing_count | missing_rate |
| --------------------------------- | ---- | --------------- | -------------- | ------------- | ------------ |
| figurative-language               | 1260 | 0               | 0.0000         | 1260          | 1.0000       |
| units-and-measurement             | 870  | 0               | 0.0000         | 870           | 1.0000       |
| reference-skills                  | 724  | 0               | 0.0000         | 724           | 1.0000       |
| punctuation                       | 514  | 0               | 0.0000         | 514           | 1.0000       |
| grammar                           | 379  | 0               | 0.0000         | 379           | 1.0000       |
| verbs                             | 251  | 0               | 0.0000         | 251           | 1.0000       |
| capitalization                    | 198  | 0               | 0.0000         | 198           | 1.0000       |
| phonological-awareness            | 97   | 0               | 0.0000         | 97            | 1.0000       |
| civics                            | 126  | 8               | 0.0635         | 118           | 0.9365       |
| writing-strategies                | 1650 | 139             | 0.0842         | 1511          | 0.9158       |
| vocabulary                        | 162  | 24              | 0.1481         | 138           | 0.8519       |
| economics                         | 682  | 298             | 0.4370         | 384           | 0.5630       |
| chemistry                         | 1194 | 536             | 0.4489         | 658           | 0.5511       |
| word-study                        | 39   | 19              | 0.4872         | 20            | 0.5128       |
| biology                           | 4098 | 2103            | 0.5132         | 1995          | 0.4868       |
| reading-comprehension             | 84   | 46              | 0.5476         | 38            | 0.4524       |
| physics                           | 3215 | 2202            | 0.6849         | 1013          | 0.3151       |
| science-and-engineering-practices | 924  | 635             | 0.6872         | 289           | 0.3128       |
| earth-science                     | 1152 | 827             | 0.7179         | 325           | 0.2821       |
| world-history                     | 65   | 53              | 0.8154         | 12            | 0.1846       |

### Low-MNAR Topic 候选

| topic                             | n    | has_image_count | has_image_rate | missing_count | missing_rate |
| --------------------------------- | ---- | --------------- | -------------- | ------------- | ------------ |
| geography                         | 2956 | 2944            | 0.9959         | 12            | 0.0041       |
| us-history                        | 510  | 467             | 0.9157         | 43            | 0.0843       |
| literacy-in-science               | 34   | 29              | 0.8529         | 5             | 0.1471       |
| world-history                     | 65   | 53              | 0.8154         | 12            | 0.1846       |
| earth-science                     | 1152 | 827             | 0.7179         | 325           | 0.2821       |
| science-and-engineering-practices | 924  | 635             | 0.6872         | 289           | 0.3128       |
| physics                           | 3215 | 2202            | 0.6849         | 1013          | 0.3151       |
| reading-comprehension             | 84   | 46              | 0.5476         | 38            | 0.4524       |
| biology                           | 4098 | 2103            | 0.5132         | 1995          | 0.4868       |
| word-study                        | 39   | 19              | 0.4872         | 20            | 0.5128       |
| chemistry                         | 1194 | 536             | 0.4489         | 658           | 0.5511       |
| economics                         | 682  | 298             | 0.4370         | 384           | 0.5630       |
| vocabulary                        | 162  | 24              | 0.1481         | 138           | 0.8519       |
| writing-strategies                | 1650 | 139             | 0.0842         | 1511          | 0.9158       |
| civics                            | 126  | 8               | 0.0635         | 118           | 0.9365       |
| figurative-language               | 1260 | 0               | 0.0000         | 1260          | 1.0000       |
| units-and-measurement             | 870  | 0               | 0.0000         | 870           | 1.0000       |
| reference-skills                  | 724  | 0               | 0.0000         | 724           | 1.0000       |
| punctuation                       | 514  | 0               | 0.0000         | 514           | 1.0000       |
| grammar                           | 379  | 0               | 0.0000         | 379           | 1.0000       |

## 12. RC2 后续判断

初步支持结构性缺失：完整元数据模型优于 subject-only。

注意：Exp0 不能把缺图直接等同于 `structural_absence`。缺失类型必须通过后续 300-500 条样本标注确认。
