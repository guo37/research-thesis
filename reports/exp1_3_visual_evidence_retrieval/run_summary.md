# Exp1.3 AI2D 图像证据检索 Baseline

## 目标

在已缓存的 AI2D diagram 图像上运行 CLIP / SigLIP 图文检索，评估题目文本是否能检索到对应图像证据，并用 Exp1.2 的 wrong-image 候选池计算干扰图混淆率。

## 图像检索指标

| model | dataset | n_queries | n_images | mrr | recall_at_1 | recall_at_5 | recall_at_10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clip_vit_b32 | ai2d | 200 | 200 | 0.2605 | 0.1150 | 0.4000 | 0.5850 |
| siglip_b16_224 | ai2d | 200 | 200 | 0.1607 | 0.0700 | 0.2400 | 0.3800 |

## Wrong-image 指标

| model | strategy | pairs | queries | wrong_image_confusion_rate | mean_positive_margin |
| --- | --- | --- | --- | --- | --- |
| clip_vit_b32 | lexical_wrong_image | 1000 | 200 | 0.4420 | 0.0233 |
| clip_vit_b32 | random_wrong_image | 1000 | 200 | 0.0860 | 0.0639 |
| clip_vit_b32 | same_skill_wrong_image | 1000 | 200 | 0.4420 | 0.0233 |
| clip_vit_b32 | same_topic_wrong_image | 1000 | 200 | 0.4420 | 0.0233 |
| siglip_b16_224 | lexical_wrong_image | 1000 | 200 | 0.4990 | 0.0134 |
| siglip_b16_224 | random_wrong_image | 1000 | 200 | 0.2230 | 0.0335 |
| siglip_b16_224 | same_skill_wrong_image | 1000 | 200 | 0.4990 | 0.0134 |
| siglip_b16_224 | same_topic_wrong_image | 1000 | 200 | 0.4990 | 0.0134 |

## 下一步

1. 抽查 CLIP / SigLIP 的 wrong-image 混淆样例，区分题干相似、图示相似和标签重复三类错误。
2. 将图像检索结果接入 RC2 wrong-image / drop-image 鲁棒推理实验。
3. 后续如需提升 RC1，可加入教育 hard negative 训练或 reranker。
