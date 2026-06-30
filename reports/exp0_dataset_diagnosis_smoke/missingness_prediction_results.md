# 缺失预测结果

目标：`has_image`。

各基线按数据划分进行评估。关键比较是 `topic`、`skill` 和元数据是否优于 `majority` 与 `subject_only`。

| model               | eval_split | auc    | average_precision | f1     | accuracy | positive_rate | features                                         |
| ------------------- | ---------- | ------ | ----------------- | ------ | -------- | ------------- | ------------------------------------------------ |
| full_metadata_text  | test       | 1.0000 | 1.0000            | 0.6667 | 0.7500   | 0.5000        | subject,topic,skill,grade,text_length,word_count |
| majority            | test       | 0.5000 | 0.5000            | 0.0000 | 0.5000   | 0.5000        | subject                                          |
| skill_only          | test       | 0.5000 | 0.5000            | 0.6667 | 0.5000   | 0.5000        | skill                                            |
| subject_only        | test       | 1.0000 | 1.0000            | 1.0000 | 1.0000   | 0.5000        | subject                                          |
| subject_topic_skill | test       | 1.0000 | 1.0000            | 1.0000 | 1.0000   | 0.5000        | subject,topic,skill                              |
| topic_only          | test       | 0.8750 | 0.8333            | 0.6667 | 0.7500   | 0.5000        | topic                                            |
| topic_skill         | test       | 0.8750 | 0.8333            | 0.6667 | 0.7500   | 0.5000        | topic,skill                                      |
| full_metadata_text  | validation | 1.0000 | 1.0000            | 1.0000 | 1.0000   | 0.5000        | subject,topic,skill,grade,text_length,word_count |
| majority            | validation | 0.5000 | 0.5000            | 0.0000 | 0.5000   | 0.5000        | subject                                          |
| skill_only          | validation | 0.5000 | 0.5000            | 0.6667 | 0.5000   | 0.5000        | skill                                            |
| subject_only        | validation | 1.0000 | 1.0000            | 1.0000 | 1.0000   | 0.5000        | subject                                          |
| subject_topic_skill | validation | 1.0000 | 1.0000            | 1.0000 | 1.0000   | 0.5000        | subject,topic,skill                              |
| topic_only          | validation | 0.5000 | 0.5000            | 0.0000 | 0.5000   | 0.5000        | topic                                            |
| topic_skill         | validation | 0.5000 | 0.5000            | 0.0000 | 0.5000   | 0.5000        | topic,skill                                      |
