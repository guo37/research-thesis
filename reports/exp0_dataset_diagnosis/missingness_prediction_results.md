# Missingness Prediction Results

Target: `has_image`.

Baselines are evaluated by split. The key comparison is whether `topic`, `skill`, and metadata improve over `majority` and `subject_only`.

| model               | eval_split | auc    | average_precision | f1     | accuracy | positive_rate | features                                         |
| ------------------- | ---------- | ------ | ----------------- | ------ | -------- | ------------- | ------------------------------------------------ |
| full_metadata_text  | test       | 0.9997 | 0.9996            | 0.9902 | 0.9906   | 0.4756        | subject,topic,skill,grade,text_length,word_count |
| majority            | test       | 0.5000 | 0.4756            | 0.0000 | 0.5244   | 0.4756        | subject                                          |
| skill_only          | test       | 0.9997 | 0.9996            | 0.9896 | 0.9901   | 0.4756        | skill                                            |
| subject_only        | test       | 0.7985 | 0.7124            | 0.7650 | 0.7142   | 0.4756        | subject                                          |
| subject_topic_skill | test       | 0.9996 | 0.9994            | 0.9909 | 0.9913   | 0.4756        | subject,topic,skill                              |
| topic_only          | test       | 0.8833 | 0.8509            | 0.7951 | 0.7791   | 0.4756        | topic                                            |
| topic_skill         | test       | 0.9997 | 0.9995            | 0.9909 | 0.9913   | 0.4756        | topic,skill                                      |
| full_metadata_text  | validation | 0.9998 | 0.9998            | 0.9917 | 0.9917   | 0.4945        | subject,topic,skill,grade,text_length,word_count |
| majority            | validation | 0.5000 | 0.4945            | 0.0000 | 0.5055   | 0.4945        | subject                                          |
| skill_only          | validation | 0.9996 | 0.9995            | 0.9883 | 0.9884   | 0.4945        | skill                                            |
| subject_only        | validation | 0.7955 | 0.7281            | 0.7718 | 0.7142   | 0.4945        | subject                                          |
| subject_topic_skill | validation | 0.9996 | 0.9995            | 0.9913 | 0.9913   | 0.4945        | subject,topic,skill                              |
| topic_only          | validation | 0.8693 | 0.8463            | 0.7906 | 0.7649   | 0.4945        | topic                                            |
| topic_skill         | validation | 0.9996 | 0.9995            | 0.9910 | 0.9910   | 0.4945        | topic,skill                                      |
