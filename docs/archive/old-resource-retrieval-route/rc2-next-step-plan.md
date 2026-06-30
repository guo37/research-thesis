# RC2 下一步计划

最后更新：2026-06-30

## 当前证据

Exp0 表明 ScienceQA 的图像缺失与 subject/topic/skill 元数据存在强结构关联。

Exp0.1 标签分析显示：

- 候选集共 372 条已标注样本。
- 其中 322 条为缺图样本。
- 230 / 322 条缺图样本被标为 `structural_absence`。
- 92 / 322 条缺图样本被标为 `accidental_missing`。
- 0 / 322 条缺图样本仍为 `ambiguous`。

## 判断

使用二分类 RC2 门控：

```text
structural_absence = 跳过补全
accidental_missing = 需要图但数据中缺图
```

这样可以让论文表述更稳妥：

> 教育多模态资源存在结构性缺失；选择性补全应先判断缺失模态是否具有教学必要性，而不是对所有缺失模态一概补全。

## Exp0.2 设计

输入：

```text
data/scienceqa/annotation/missing_type_annotation_candidates.csv
```

样本：

- 只使用 `has_image = 0` 的行。

目标：

```text
y = 1 if human_label == accidental_missing
y = 0 if human_label == structural_absence
```

基线：

1. 多数类基线。
2. 仅元数据模型：subject、topic、skill、grade、text_length。
3. 仅文本模型：question、choices、hint、lecture、solution。
4. 元数据 + 文本模型。

指标：

- Balanced accuracy。
- Macro F1。
- 正类 F1。
- PR-AUC.
- 混淆矩阵。

最低成功条件：

> 元数据 + 文本模型必须在正类 F1 或 PR-AUC 上超过多数类基线和仅元数据模型。

## Exp0.2 第一版结果

第一版基线在原始 ScienceQA 划分上达到完美测试指标。

这只能视为可行性信号，不能作为最终论文证据，因为 topic/skill 重叠可能让任务比真实泛化测试更容易。

下一步验证：

1. 留出完整 topic 作为测试。
2. 在标签数量允许时，留出完整 skill 作为测试。
3. 在分组划分下比较仅元数据、仅文本、元数据+文本模型。
4. 完成上述验证后，再把门控应用到全部 ScienceQA 缺图样本。

## 论文使用前

写入论文前，需要抽查：

1. 一部分 `accidental_missing` 样本。
2. language/social/natural science 中的 `structural_absence` 样本。
3. topic/skill 组合异常的样本。
