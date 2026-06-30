# 研究工作空间

这个仓库是毕业论文研究项目的可同步工作空间：

> 面向教育图文问答的模态证据对齐检索与鲁棒推理方法研究

当前项目状态主要围绕 ScienceQA 的 Exp0/Exp0.1/Exp0.2 和 Exp1.0：

- Exp0：诊断图像可用性是否受教育元数据结构性影响。
- Exp0.1：构建缺失类型标注候选集，用于人工标注。
- Exp0.2：构建 `structural_absence` vs `accidental_missing` 门控 pilot。
- Exp1.0：建立教育图文证据统一 schema，当前已生成 ScienceQA、TQA / CK12 和 AI2D 样例。

开始新的研究工作前，先查看 [docs/research-dashboard.md](docs/research-dashboard.md) 和 [docs/current-research-plan.md](docs/current-research-plan.md)。

## 目录说明

```text
configs/                  实验配置文件。
data/scienceqa/processed/ 当前报告使用的可复现实验处理表。
data/scienceqa/annotation/标注候选集和人工标注批次。
reports/                  实验报告和结果解读。
scripts/                  可复现实验脚本和报告生成脚本。
tests/                    小型测试样例和回归检查。
docs/                     工作空间管理、同步、模板和研究规划文档。
```

不要提交本地凭证或大型缓存文件。`data/**/cache/` 和 `*.pem` 已被忽略。

## 标准工作流程

在任意电脑开始工作：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync_start.ps1
```

在 Mac 上：

```bash
bash scripts/sync_start.sh
```

切换设备前结束并同步工作：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync_finish.ps1 -Message "describe the research change"
```

在 Mac 上：

```bash
bash scripts/sync_finish.sh "describe the research change"
```

如果还没有配置远端仓库，先创建一个私有 Git 仓库，然后运行：

```powershell
git remote add origin <private-repo-url>
git push -u origin main
```

## 复现 Exp0

使用 Conda 或 pip 安装依赖：

```powershell
conda env create -f environment_exp0.yml
conda activate scienceqa-exp0
```

或者：

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements_exp0.txt
```

运行数据诊断：

```powershell
python scripts/exp0_dataset_diagnosis.py --config configs/exp0_scienceqa.yaml
python scripts/exp0_1_build_missing_type_candidates.py --config configs/exp0_1_missing_type_annotation.yaml
```
