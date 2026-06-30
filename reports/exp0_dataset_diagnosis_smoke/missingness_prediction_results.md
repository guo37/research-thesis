# Missingness Prediction Results

Target: `has_image`.

Baselines are evaluated by split. The key comparison is whether `topic`, `skill`, and metadata improve over `majority` and `subject_only`.

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
