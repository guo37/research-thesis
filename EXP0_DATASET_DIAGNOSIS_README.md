# Exp0：ScienceQA 数据集诊断

本实验用于检查 ScienceQA 中图像是否存在，是否受到教育元数据的结构性影响。

核心问题：

```text
ScienceQA 中的图像缺失是否依赖 subject / topic / skill / grade / text_length？
```

第一次运行只生成 `has_image = 1 / 0`。它不会直接标注 `structural_absence`，因为这需要后续小规模人工标注。

## 推荐使用的现有环境

本地 `my_research` conda 环境已经包含第一阶段所需依赖：

```powershell
conda activate my_research
python scripts/exp0_dataset_diagnosis.py --config configs/exp0_scienceqa.yaml
```

如果需要一个干净的新环境：

```powershell
conda env create -f environment_exp0.yml
conda activate scienceqa-exp0
python scripts/exp0_dataset_diagnosis.py --config configs/exp0_scienceqa.yaml
```

## 本地数据模式

如果 ScienceQA 已经下载到本地，可以运行：

```powershell
python scripts/exp0_dataset_diagnosis.py --input-dir data/scienceqa/raw
python scripts/exp0_dataset_diagnosis.py --input-file data/scienceqa/raw/scienceqa.csv
```

脚本支持 `.csv`、`.json`、`.jsonl` 和 `.parquet`。如果输入目录，脚本会按 `train.*`、`validation.*`、`val.*`、`dev.*`、`test.*` 识别数据划分。其他受支持文件如果没有 `split` 列，会被视为 `unknown` 划分。

## 输出文件

```text
data/scienceqa/processed/resources.csv
data/scienceqa/processed/concepts.csv
data/scienceqa/processed/resource_concept_edges.csv
data/scienceqa/processed/concept_edges.csv
data/scienceqa/processed/modality_status_initial.csv

reports/exp0_dataset_diagnosis/dataset_statistics.md
reports/exp0_dataset_diagnosis/missingness_by_subject.csv
reports/exp0_dataset_diagnosis/missingness_by_topic.csv
reports/exp0_dataset_diagnosis/missingness_by_skill.csv
reports/exp0_dataset_diagnosis/missingness_prediction_results.md
reports/exp0_dataset_diagnosis/prediction_results.csv
reports/exp0_dataset_diagnosis/high_mnar_topics.csv
reports/exp0_dataset_diagnosis/low_mnar_topics.csv
```

## Exp0.1 缺失类型标注候选集

生成正式 Exp0 报告后，构建人工标注候选表：

```powershell
conda run -n my_research python scripts/exp0_1_build_missing_type_candidates.py --config configs/exp0_1_missing_type_annotation.yaml
```

该命令会生成：

```text
data/scienceqa/annotation/missing_type_annotation_candidates.csv
reports/exp0_1_missing_type_annotation/annotation_candidate_summary.md
```

`suggested_missing_type` 只是抽样提示。人工标签应从 `observed`、`accidental_missing`、`structural_absence`、`ambiguous` 中选择。
