# 研究空间地图

本仓库作为可执行研究工作空间使用。Obsidian 或外部笔记用于更高层的知识索引；可运行代码、实验配置、生成报告和当前论文规划应保存在这里。

## 三个研究区域

### 1. 实验

目标：让每个实验都能在家用 Windows、办公 Windows 和 Mac 上复现。

当前目录：

- `configs/`：实验脚本参数文件。
- `scripts/`：可执行研究脚本。
- `tests/`：测试样例和基础检查。
- `data/scienceqa/processed/`：当前分析需要同步的处理后表格。
- `data/scienceqa/annotation/`：标注候选集和批次文件。
- `reports/`：生成的实验报告和结果解读。

规则：

- `data/**/cache/` 只保留在本地。
- 原始数据或下载数据不要进 Git，除非只是很小的测试样例。
- 每个新的主要实验都创建 `configs/expN_*.yaml`、`reports/expN_*` 和简短运行记录。
- 小型稳定测试样例放入 `tests/fixtures/`。

### 2. 论文写作

目标：维护研究主线和论文交付材料。

当前文件：

- `PAPER_OUTLINE_REVISED.md`
- `论文重构_最终主线与实施方案.md`
- `研究重构_文献综述与技术路线.md`

写作内容增加后，建议新增目录：

```text
paper/
  proposal/
  midterm/
  thesis/
  literature/
  review/
```

规则：

- 用一个规范大纲文件维护最新论文主线。
- 文献笔记应关联 Zotero citation key。
- 生成报告作为证据使用，不直接当成论文正文。

### 3. 组会

目标：形成可复用的两周研究汇报流程。

推荐目录：

```text
meetings/
  2026-07-xx/
    summary.md
    slides.pptx
    figures/
```

规则：

- 每次组会总结都应回答：上阶段进展、证据/结果、阻塞点、未来两周计划。
- 如果提交幻灯片，`.pptx` 会由 Git LFS 处理。

## 同步策略

提交到 Git：

- 代码、配置、测试、Markdown 笔记、小型 CSV 报告、标注批次。

不要提交到 Git：

- `*.pem`、`.env*`、下载缓存、模型 checkpoint、大型原始数据集、虚拟环境。

后续用 Git LFS 管理：

- PPT/Word/PDF 交付文件、模型权重、压缩归档数据集。

后续用 DVC 管理：

- 需要版本化的原始数据集、大型实验输出、模型 checkpoint、可复现实验流水线。
