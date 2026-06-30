# 实验运行记录

## 元数据

- 日期：2026-07-01
- 实验：Exp1.3 AI2D 图像证据检索 baseline
- 分支：main
- 提交：当前工作区未提交
- 设备：Mac / Codex desktop
- 环境：Codex bundled Python + 临时依赖目录 `/private/tmp/research_exp1_visual_deps`

## 研究问题

开放域 CLIP 是否能在 AI2D 教育图示问答样例中，根据题目文本检索到正确 diagram？在 Exp1.2 构造的 wrong-image 候选池中，CLIP 是否会被题干相似但图像错误的候选干扰？

## 配置

- 配置文件：`configs/exp1_3_visual_evidence_retrieval.yaml`
- 数据集：AI2D schema sample
- 输入路径：`data/educational_mm/schema_samples/ai2d_schema_sample.csv`
- 图像缓存：`data/ai2d/raw/images`
- 输出路径：`reports/exp1_3_visual_evidence_retrieval/`

## 命令

```bash
HF_HOME=/private/tmp/research_hf_cache PYTHONPATH=/private/tmp/research_exp1_visual_deps \
/Users/xcs/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
scripts/exp1_3_cache_ai2d_images.py --config configs/exp1_3_visual_evidence_retrieval.yaml

HF_HOME=/private/tmp/research_hf_cache PYTHONPATH=/private/tmp/research_exp1_visual_deps \
/Users/xcs/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
scripts/exp1_3_visual_evidence_retrieval.py --config configs/exp1_3_visual_evidence_retrieval.yaml
```

## 结果

- AI2D 图像缓存：200 / 200。
- CLIP ViT-B/32：Recall@1 = 0.1150，Recall@5 = 0.4000，Recall@10 = 0.5850，MRR = 0.2605。
- SigLIP B/16 224：Recall@1 = 0.0700，Recall@5 = 0.2400，Recall@10 = 0.3800，MRR = 0.1607。
- CLIP random wrong-image confusion rate：0.0860。
- CLIP lexical / same-topic / same-skill wrong-image confusion rate：0.4420。
- SigLIP random wrong-image confusion rate：0.2230。
- SigLIP lexical / same-topic / same-skill wrong-image confusion rate：0.4990。

## 解读

CLIP 在随机干扰图上还能保持较低混淆，但面对题干词面相近的图示时混淆率显著升高。SigLIP 在当前 AI2D 样例上整体弱于 CLIP，wrong-image 混淆更高。这个结果支持 RC1 的问题设定：教育图文证据检索不能只依赖开放域图文相似度，还需要教学目标或 hard negative 约束。

## 下一步

抽查 CLIP / SigLIP 的 wrong-image 混淆样例，并把这些样例接入 RC2 的 wrong-image / drop-image 鲁棒推理实验设计。
