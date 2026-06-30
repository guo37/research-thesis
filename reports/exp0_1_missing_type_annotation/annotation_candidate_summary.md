# Exp0.1 缺失类型标注候选集汇总

- 候选样本数：372
- 来源资源表：data\scienceqa\processed\resources.csv
- 最小分组样本数：20
- 高缺失率阈值：0.9
- 低缺失率阈值：0.2

## 候选类型计数

| candidate_type               | n   |
| ---------------------------- | --- |
| structural_absence_candidate | 150 |
| ambiguous_missing_candidate  | 100 |
| accidental_missing_candidate | 72  |
| observed_reference           | 50  |

## 数据划分计数

| suggested_missing_type       | split      | n   |
| ---------------------------- | ---------- | --- |
| accidental_missing_candidate | test       | 15  |
| accidental_missing_candidate | train      | 42  |
| accidental_missing_candidate | validation | 15  |
| ambiguous_missing_candidate  | test       | 18  |
| ambiguous_missing_candidate  | train      | 58  |
| ambiguous_missing_candidate  | validation | 24  |
| observed_reference           | test       | 7   |
| observed_reference           | train      | 33  |
| observed_reference           | validation | 10  |
| structural_absence_candidate | test       | 25  |
| structural_absence_candidate | train      | 90  |
| structural_absence_candidate | validation | 35  |

## 各候选类型的主要 Topic

| suggested_missing_type       | topic                             | n   |
| ---------------------------- | --------------------------------- | --- |
| accidental_missing_candidate | us-history                        | 43  |
| accidental_missing_candidate | geography                         | 12  |
| accidental_missing_candidate | world-history                     | 12  |
| accidental_missing_candidate | literacy-in-science               | 5   |
| ambiguous_missing_candidate  | biology                           | 95  |
| ambiguous_missing_candidate  | chemistry                         | 3   |
| ambiguous_missing_candidate  | economics                         | 2   |
| observed_reference           | geography                         | 14  |
| observed_reference           | biology                           | 10  |
| observed_reference           | physics                           | 8   |
| observed_reference           | science-and-engineering-practices | 5   |
| observed_reference           | earth-science                     | 4   |
| observed_reference           | chemistry                         | 3   |
| observed_reference           | reading-comprehension             | 2   |
| observed_reference           | us-history                        | 2   |
| observed_reference           | economics                         | 1   |
| observed_reference           | writing-strategies                | 1   |
| structural_absence_candidate | biology                           | 33  |
| structural_absence_candidate | figurative-language               | 22  |
| structural_absence_candidate | writing-strategies                | 18  |
| structural_absence_candidate | physics                           | 14  |
| structural_absence_candidate | reference-skills                  | 13  |
| structural_absence_candidate | units-and-measurement             | 11  |
| structural_absence_candidate | chemistry                         | 9   |
| structural_absence_candidate | punctuation                       | 8   |
| structural_absence_candidate | earth-science                     | 4   |
| structural_absence_candidate | economics                         | 4   |

## 标注说明

`suggested_missing_type` 仅作为抽样提示。请将 `human_label` 填为以下之一：

- `observed`
- `accidental_missing`
- `structural_absence`
- `ambiguous`

不要仅根据 `has_image=0` 推断 `structural_absence`；需要判断图像对理解或解题是否具有教学必要性。
