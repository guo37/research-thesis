# Exp1.3 AI2D 图像缓存

## 目标

为 AI2D schema 样例补齐本地图像缓存，给后续 CLIP / SigLIP 图文证据检索提供实际图像文件。

## 缓存状态

| status | rows |
| --- | --- |
| cached | 200 |

## 输出

- manifest：`reports/exp1_3_visual_evidence_retrieval/ai2d_image_manifest.csv`
- image cache：`data/ai2d/raw/images`

## 样例

| sample_id | local_image_path | width | height |
| --- | --- | --- | --- |
| ai2d_test_000001 | data/ai2d/raw/images/ai2d_test_000001.png | 400 | 250 |
| ai2d_test_000002 | data/ai2d/raw/images/ai2d_test_000002.png | 400 | 250 |
| ai2d_test_000003 | data/ai2d/raw/images/ai2d_test_000003.png | 400 | 250 |
| ai2d_test_000004 | data/ai2d/raw/images/ai2d_test_000004.png | 1001 | 817 |
| ai2d_test_000005 | data/ai2d/raw/images/ai2d_test_000005.png | 1001 | 817 |
| ai2d_test_000006 | data/ai2d/raw/images/ai2d_test_000006.png | 1136 | 720 |
| ai2d_test_000007 | data/ai2d/raw/images/ai2d_test_000007.png | 1136 | 720 |
| ai2d_test_000008 | data/ai2d/raw/images/ai2d_test_000008.png | 1136 | 720 |
| ai2d_test_000009 | data/ai2d/raw/images/ai2d_test_000009.png | 1136 | 720 |
| ai2d_test_000010 | data/ai2d/raw/images/ai2d_test_000010.png | 1136 | 720 |

## 下一步

1. 使用 `scripts/exp1_3_visual_evidence_retrieval.py` 运行 CLIP / SigLIP 图文检索。
2. 将 `wrong_image_candidates.csv` 作为 wrong-image confusion 评测候选池。
