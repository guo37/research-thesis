# Exp0: ScienceQA Dataset Diagnosis

This experiment checks whether ScienceQA image availability has structured dependence on educational metadata.

Primary question:

```text
Does image missingness in ScienceQA depend on subject / topic / skill / grade / text_length?
```

The first run only creates `has_image = 1 / 0`. It does not label `structural_absence`, because that requires later small-scale annotation.

## Recommended Existing Environment

The local `my_research` conda environment already contains the required first-stage packages:

```powershell
conda activate my_research
python scripts/exp0_dataset_diagnosis.py --config configs/exp0_scienceqa.yaml
```

If you want a clean environment:

```powershell
conda env create -f environment_exp0.yml
conda activate scienceqa-exp0
python scripts/exp0_dataset_diagnosis.py --config configs/exp0_scienceqa.yaml
```

## Local Data Mode

If ScienceQA has already been downloaded, run one of:

```powershell
python scripts/exp0_dataset_diagnosis.py --input-dir data/scienceqa/raw
python scripts/exp0_dataset_diagnosis.py --input-file data/scienceqa/raw/scienceqa.csv
```

The script accepts `.csv`, `.json`, `.jsonl`, and `.parquet`. For a directory, it reads files named like `train.*`, `validation.*`, `val.*`, `dev.*`, and `test.*` as splits. Other supported files are read as `unknown` split unless they contain a `split` column.

## Outputs

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

## Exp0.1 Missing-Type Annotation Candidates

After the formal Exp0 report is generated, build the manual annotation candidate table:

```powershell
conda run -n my_research python scripts/exp0_1_build_missing_type_candidates.py --config configs/exp0_1_missing_type_annotation.yaml
```

This creates:

```text
data/scienceqa/annotation/missing_type_annotation_candidates.csv
reports/exp0_1_missing_type_annotation/annotation_candidate_summary.md
```

`suggested_missing_type` is only a sampling hint. Human labels should be one of `observed`, `accidental_missing`, `structural_absence`, or `ambiguous`.
