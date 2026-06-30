# Research Workspace

This repository is the syncable workspace for the thesis research project:

> 面向教育资源检索的可信多模态知识推理研究

The current project state focuses on ScienceQA Exp0/Exp0.1:

- Exp0: diagnose whether image availability is structured by educational metadata.
- Exp0.1: build missing-type annotation candidates for manual labeling.
- Paper planning: keep the revised thesis outline, literature route, and final implementation plan.

Start from [docs/research-dashboard.md](docs/research-dashboard.md) before planning new research work.

## Directory Map

```text
configs/                  Experiment configuration files.
data/scienceqa/processed/ Reproducible processed tables used by current reports.
data/scienceqa/annotation/Annotation candidates and manual labeling batches.
reports/                  Experiment reports and interpretation notes.
scripts/                  Reproducible experiment and reporting scripts.
tests/                    Small fixtures and regression checks.
docs/                     Workspace management, sync, templates, and research planning notes.
```

Do not commit local credentials or heavyweight cache files. `data/**/cache/` and `*.pem` are ignored.

## Standard Workflow

Start work on any computer:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync_start.ps1
```

On Mac:

```bash
bash scripts/sync_start.sh
```

Finish work before switching devices:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync_finish.ps1 -Message "describe the research change"
```

On Mac:

```bash
bash scripts/sync_finish.sh "describe the research change"
```

If a remote has not been configured yet, create a private Git repository and run:

```powershell
git remote add origin <private-repo-url>
git push -u origin main
```

## Reproduce Exp0

Install dependencies with either Conda or pip:

```powershell
conda env create -f environment_exp0.yml
conda activate scienceqa-exp0
```

or:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements_exp0.txt
```

Run the diagnosis:

```powershell
python scripts/exp0_dataset_diagnosis.py --config configs/exp0_scienceqa.yaml
python scripts/exp0_1_build_missing_type_candidates.py --config configs/exp0_1_missing_type_annotation.yaml
```
