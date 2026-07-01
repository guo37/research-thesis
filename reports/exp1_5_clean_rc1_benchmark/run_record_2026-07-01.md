# 实验运行记录

## 元数据

- 日期：2026-07-01
- 实验：Exp1.5 clean RC1 benchmark
- 分支：main
- 提交：运行后填写
- 设备：Windows
- 环境：my_research

## 研究问题

把 RC1 的文本和图像证据检索评测切换为无泄漏、固定负样本数、diagram-level 去重的干净 benchmark。

## 配置

- 配置文件：configs/exp1_5_clean_rc1_benchmark.yaml
- 数据集：ScienceQA、TQA / CK12、AI2D schema samples
- 输入路径：data/educational_mm/schema_samples，reports/exp1_3_visual_evidence_retrieval
- 输出路径：reports/exp1_5_clean_rc1_benchmark

## 命令

```powershell
conda run -n my_research python scripts/exp1_5_clean_rc1_benchmark.py --config configs/exp1_5_clean_rc1_benchmark.yaml
```

## 结果

- 主要指标：见 run_summary.md、text_pair_metrics.csv、visual_pair_metrics.csv。
- 基线：TF-IDF / BM25 文本打分，CLIP / SigLIP wrong-image 分数复用 Exp1.3。
- 对比：no-solution 文本证据、固定 hard negative、nonduplicate wrong image。

## 解读

见 run_summary.md。

## 下一步

基于 rc1_text_benchmark_pairs.csv 训练 evidence alignment scorer。
