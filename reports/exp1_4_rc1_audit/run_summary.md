# Exp1.4 RC1 审计与消融

## 目标

在进入 RC2 之前，审计 RC1 结果是否受到答案泄漏、字段选择、候选池大小和重复图像的影响。

## 审计结论

- 当前 RC1 结果应表述为 baseline / evaluation audit，不应表述为已完成训练后的方法提升。
- ScienceQA `solution` 会带来明显答案泄漏风险，必须使用 `no_solution` 或更干净的证据字段重跑主结果。
- hard negative 的指标必须在固定候选池大小和共同 query 子集上解释，否则不能和 full-corpus baseline 直接对比。
- AI2D 需要按 diagram hash 去重评估；同一张 diagram 的不同题不能互相当 wrong image。

## Evidence 泄漏与重复

| dataset | evidence_variant | n_rows | unique_evidence | duplicate_groups | max_duplicate_group | correct_option_in_evidence_rate | any_option_in_evidence_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| scienceqa | full | 198 | 190 | 7 | 3 | 0.7323 | 0.7576 |
| scienceqa | no_solution | 169 | 128 | 28 | 6 | 0.2130 | 0.2308 |
| scienceqa | hint_lecture | 169 | 128 | 28 | 6 | 0.2130 | 0.2308 |
| scienceqa | solution_only | 185 | 177 | 7 | 3 | 0.7784 | 0.7946 |
| tqa_ck12 | full | 200 | 9 | 8 | 38 | 0.0200 | 0.0000 |
| tqa_ck12 | no_solution | 200 | 9 | 8 | 38 | 0.0200 | 0.0000 |
| tqa_ck12 | hint_lecture | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 |
| tqa_ck12 | solution_only | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 |

## ScienceQA Evidence 消融

| evidence_variant | n_queries | n_corpus | recall_at_1 | mrr |
| --- | --- | --- | --- | --- |
| full | 198.0000 | 190.0000 | 0.8889 | 0.9340 |
| no_solution | 169.0000 | 128.0000 | 0.7041 | 0.8113 |
| hint_lecture | 169.0000 | 128.0000 | 0.7041 | 0.8113 |
| solution_only | 185.0000 | 177.0000 | 0.8757 | 0.9311 |

## ScienceQA Query 消融

| query_variant | n_queries | n_corpus | recall_at_1 | mrr |
| --- | --- | --- | --- | --- |
| question_only | 169.0000 | 128.0000 | 0.5799 | 0.6887 |
| question_choices | 169.0000 | 128.0000 | 0.6036 | 0.7182 |
| question_choices_topic_skill | 169.0000 | 128.0000 | 0.7041 | 0.8113 |

## 等大小 Hard Negative 审计

| strategy | n_queries | fixed_negatives | recall_at_1 | mrr | top1_error_rate |
| --- | --- | --- | --- | --- | --- |
| random | 152.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| same_subject | 152.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| same_topic | 152.0000 | 1.0000 | 0.9737 | 0.9868 | 0.0263 |
| same_skill | 152.0000 | 1.0000 | 0.9276 | 0.9638 | 0.0724 |

## AI2D Diagram 去重审计

| model | n_queries | diagram_group_recall_at_1 | diagram_group_recall_at_5 | diagram_group_recall_at_10 | diagram_group_mrr_at_10 | cached_images | unique_diagram_hashes | duplicate_groups | images_in_duplicate_groups | max_duplicate_group |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clip_vit_b32 | 200 | 0.2850 | 0.4700 | 0.6500 | 0.3740 | 200 | 86 | 53 | 167 | 11 |
| siglip_b16_224 | 200 | 0.1600 | 0.2750 | 0.4000 | 0.2176 | 200 | 86 | 53 | 167 | 11 |

## AI2D Wrong-image 去重审计

| model | strategy | pairs | same_diagram_pairs | confusion_rate_all_pairs | confusion_rate_nonduplicate_pairs | nonduplicate_pairs |
| --- | --- | --- | --- | --- | --- | --- |
| clip_vit_b32 | lexical_wrong_image | 1000 | 259 | 0.4420 | 0.2470 | 741 |
| clip_vit_b32 | random_wrong_image | 1000 | 17 | 0.0860 | 0.0702 | 983 |
| clip_vit_b32 | same_skill_wrong_image | 1000 | 259 | 0.4420 | 0.2470 | 741 |
| clip_vit_b32 | same_topic_wrong_image | 1000 | 259 | 0.4420 | 0.2470 | 741 |
| siglip_b16_224 | lexical_wrong_image | 1000 | 259 | 0.4990 | 0.3239 | 741 |
| siglip_b16_224 | random_wrong_image | 1000 | 17 | 0.2230 | 0.2096 | 983 |
| siglip_b16_224 | same_skill_wrong_image | 1000 | 259 | 0.4990 | 0.3239 | 741 |
| siglip_b16_224 | same_topic_wrong_image | 1000 | 259 | 0.4990 | 0.3239 | 741 |

## 复查原因

1. ScienceQA 文本 evidence 的高指标一部分来自 `solution` 字段，属于数据构造导致的泄漏风险。
2. Exp1.2 random hard negative 指标高于 Exp1.1，主要因为候选池从完整 corpus 缩小为 `1 + N` 候选，不是模型训练提升。
3. TQA / CK12 的文本 evidence 只有少量唯一 lesson/instruction，当前只能作为流程连通性验证。
4. AI2D 多题共用同一 diagram，sample-level 图像检索会误罚同图不同题，wrong-image 也会混入实际同图样本。

## 迭代优化

1. 将 RC1 主文本实验切换到 `no_solution` evidence。
2. 将 query 设置拆分为 `question_only`、`question_choices`、`question_choices_topic_skill`，论文中不要混写。
3. 将 hard negative 训练/评测固定为共同 query 子集和固定负样本数。
4. 将 AI2D 图像检索切换到 diagram-level positive set，并过滤 same-diagram wrong image。
5. 在上述干净评测上，再训练 evidence alignment scorer。
