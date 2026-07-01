# Exp1.5 Clean RC1 Benchmark

## 目标

把 RC1 从 baseline / audit 推进到可训练 scorer 的干净 benchmark：文本证据去掉 `solution`，hard negative 使用固定负样本数，AI2D 图像评测过滤 same-diagram wrong image。

## 产物

- `rc1_text_benchmark_pairs.csv`：文本 evidence alignment pair 数据，可直接用于训练/评测 scorer。
- `rc1_visual_benchmark_pairs.csv`：AI2D diagram-level image pair 数据，已过滤同 diagram 负例。
- `diagram_groups.csv`：AI2D diagram hash、重复组大小和 split。
- `text_pair_metrics.csv` / `visual_pair_metrics.csv`：固定候选池上的 baseline 指标。

## 文本 Benchmark 规模

| dataset | raw_rows | eval_rows | eligible_queries | eligible_pools | unique_evidence | evidence_variant | query_variant | fixed_negatives_per_strategy | strategies |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| scienceqa | 200 | 169 | 169 | 544 | 128 | no_solution | question_choices_topic_skill | 1 | random\|same_subject\|same_topic\|same_skill |
| tqa_ck12 | 200 | 200 | 176 | 611 | 9 | no_solution | question_choices_topic_skill | 1 | random\|same_subject\|same_topic\|same_skill |

## 文本 Pair 数量

| dataset | split | label | pairs |
| --- | --- | --- | --- |
| scienceqa | dev | 0 | 67 |
| scienceqa | dev | 1 | 67 |
| scienceqa | test | 0 | 74 |
| scienceqa | test | 1 | 74 |
| scienceqa | train | 0 | 403 |
| scienceqa | train | 1 | 403 |
| tqa_ck12 | test | 0 | 102 |
| tqa_ck12 | test | 1 | 102 |
| tqa_ck12 | train | 0 | 509 |
| tqa_ck12 | train | 1 | 509 |

## 文本 Test 指标

| dataset | negative_strategy | model | n_queries | candidate_pool_size_mean | recall_at_1 | mrr | top1_error_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| scienceqa | combined | tfidf | 27 | 3.4815 | 1.0000 | 1.0000 | 0.0000 |
| scienceqa | random | tfidf | 27 | 2.0000 | 1.0000 | 1.0000 | 0.0000 |
| scienceqa | same_subject | tfidf | 27 | 2.0000 | 1.0000 | 1.0000 | 0.0000 |
| scienceqa | same_topic | tfidf | 20 | 2.0000 | 1.0000 | 1.0000 | 0.0000 |
| tqa_ck12 | combined | tfidf | 34 | 2.0000 | 1.0000 | 1.0000 | 0.0000 |
| tqa_ck12 | random | tfidf | 34 | 2.0000 | 1.0000 | 1.0000 | 0.0000 |
| tqa_ck12 | same_skill | tfidf | 34 | 2.0000 | 1.0000 | 1.0000 | 0.0000 |
| tqa_ck12 | same_subject | tfidf | 34 | 2.0000 | 1.0000 | 1.0000 | 0.0000 |
| scienceqa | combined | bm25 | 27 | 3.4815 | 1.0000 | 1.0000 | 0.0000 |
| scienceqa | random | bm25 | 27 | 2.0000 | 1.0000 | 1.0000 | 0.0000 |
| scienceqa | same_subject | bm25 | 27 | 2.0000 | 1.0000 | 1.0000 | 0.0000 |
| scienceqa | same_topic | bm25 | 20 | 2.0000 | 1.0000 | 1.0000 | 0.0000 |
| tqa_ck12 | combined | bm25 | 34 | 2.0000 | 1.0000 | 1.0000 | 0.0000 |
| tqa_ck12 | random | bm25 | 34 | 2.0000 | 1.0000 | 1.0000 | 0.0000 |
| tqa_ck12 | same_skill | bm25 | 34 | 2.0000 | 1.0000 | 1.0000 | 0.0000 |
| tqa_ck12 | same_subject | bm25 | 34 | 2.0000 | 1.0000 | 1.0000 | 0.0000 |

## 图像 Benchmark 规模

| dataset | cached_images | unique_diagram_hashes | duplicate_groups | images_in_duplicate_groups | fixed_negatives_per_strategy | strategies |
| --- | --- | --- | --- | --- | --- | --- |
| ai2d | 200 | 86 | 53 | 167 | 1 | random_wrong_image\|lexical_wrong_image\|same_topic_wrong_image\|same_skill_wrong_image |

## AI2D Diagram Split

| split | samples | unique_diagrams |
| --- | --- | --- |
| dev | 26 | 13 |
| test | 22 | 13 |
| train | 152 | 60 |

## 图像 Pair 数量

| dataset | split | label | pairs |
| --- | --- | --- | --- |
| ai2d | dev | 0 | 41 |
| ai2d | dev | 1 | 41 |
| ai2d | test | 0 | 36 |
| ai2d | test | 1 | 36 |
| ai2d | train | 0 | 566 |
| ai2d | train | 1 | 566 |

## 图像 Test 指标

| dataset | negative_strategy | model | n_queries | candidate_pool_size_mean | recall_at_1 | mrr | top1_error_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ai2d | lexical_wrong_image | clip_vit_b32 | 9 | 2.0000 | 0.8889 | 0.9444 | 0.1111 |
| ai2d | random_wrong_image | clip_vit_b32 | 9 | 2.0000 | 1.0000 | 1.0000 | 0.0000 |
| ai2d | same_skill_wrong_image | clip_vit_b32 | 9 | 2.0000 | 0.8889 | 0.9444 | 0.1111 |
| ai2d | same_topic_wrong_image | clip_vit_b32 | 9 | 2.0000 | 0.8889 | 0.9444 | 0.1111 |
| ai2d | lexical_wrong_image | siglip_b16_224 | 9 | 2.0000 | 0.4444 | 0.7222 | 0.5556 |
| ai2d | random_wrong_image | siglip_b16_224 | 9 | 2.0000 | 0.7778 | 0.8889 | 0.2222 |
| ai2d | same_skill_wrong_image | siglip_b16_224 | 9 | 2.0000 | 0.5556 | 0.7778 | 0.4444 |
| ai2d | same_topic_wrong_image | siglip_b16_224 | 9 | 2.0000 | 0.4444 | 0.7222 | 0.5556 |
| ai2d | combined | clip_vit_b32 | 12 | 2.5833 | 0.9167 | 0.9583 | 0.0833 |
| ai2d | combined | siglip_b16_224 | 12 | 2.5833 | 0.5000 | 0.7361 | 0.5000 |

## 工作性结论

- RC1 已有干净 benchmark 入口，后续 scorer 不应再使用含 `solution` 的文本 evidence 作为主结果。
- 文本侧 split 按 evidence id 划分，图像侧 split 按 diagram hash 划分；这比 sample 随机切分更适合验证未见证据泛化。
- 当前严格同 split 文本候选在 200 条样例上偏容易，TF-IDF / BM25 测试指标接近满分；它只能作为数据构造和训练入口，不能作为方法提升结论。
- TQA / CK12 当前仍受公开 instruction 样例唯一 evidence 过少限制，只能作为流程验证；主结论应先放在 ScienceQA 和 AI2D。
- 下一步可以训练一个轻量 evidence alignment scorer，并和 TF-IDF / BM25 / CLIP / SigLIP 在同一 clean benchmark 上对比。
