# Exp0 Dataset Statistics

## 1. ScienceQA Basic Scale

- Total samples: 16
- Overall has_image rate: 0.5000
- Overall missing rate: 0.5000

## 2. Train / Validation / Test Samples

| split      | n |
| ---------- | - |
| train      | 8 |
| validation | 4 |
| test       | 4 |

## 3. Image Availability Distribution

| has_image | n | rate   |
| --------- | - | ------ |
| 1         | 8 | 0.5000 |
| 0         | 8 | 0.5000 |

## 4. Subject / Topic / Skill Distribution

| field    | unique_values | non_empty |
| -------- | ------------- | --------- |
| subject  | 2             | 16        |
| topic    | 13            | 16        |
| skill    | 16            | 16        |
| grade    | 3             | 16        |
| category | 10            | 16        |

## 5. Subject-Level Image Missing Rate

| subject          | n | has_image_count | has_image_rate | missing_count | missing_rate |
| ---------------- | - | --------------- | -------------- | ------------- | ------------ |
| language science | 7 | 0               | 0.0000         | 7             | 1.0000       |
| natural science  | 9 | 8               | 0.8889         | 1             | 0.1111       |

## 6. Topic-Level Image Missing Rate

Main-topic threshold: `topic_count >= 20`.

_No rows._

## 7. Skill-Level Image Missing Rate

Main-skill threshold: `skill_count >= 20`.

_No rows._

## 8. Mutual Information

| field   | mutual_information |
| ------- | ------------------ |
| subject | 0.9939             |
| topic   | 0.7469             |
| skill   | 0.7265             |
| grade   | 0.5753             |

## 9. Chi-Square Tests

| field   | chi2    | p_value | dof     |
| ------- | ------- | ------- | ------- |
| subject | 9.1429  | 0.0025  | 1.0000  |
| topic   | 16.0000 | 0.1912  | 12.0000 |
| skill   | 16.0000 | 0.3821  | 15.0000 |
| grade   | 9.5000  | 0.0087  | 2.0000  |

## 10. Missingness Prediction AUC

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

## 11. High-MNAR / Low-MNAR Topic Candidates

High-MNAR candidates are frequent topics with high missing rate. Low-MNAR candidates are frequent topics with low missing rate.

### High-MNAR Topic Candidates

_No rows._

### Low-MNAR Topic Candidates

_No rows._

## 12. RC2 Continuation Decision

Weak or inconclusive structured-missingness signal: full metadata does not clearly improve over subject-only.

Caveat: Exp0 does not equate missing images with `structural_absence`. Missing-type labels require the later 300-500 sample annotation step.
