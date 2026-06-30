# 组会周期

最后更新：2026-06-30

每两周组会使用一个独立文件夹。

```text
meetings/
  2026-07-xx/
    summary.md
    slides.pptx
    figures/
```

## 可用模板

- [templates/group-meeting-summary.md](templates/group-meeting-summary.md)
- [templates/组会ppt6.6.pptx](templates/组会ppt6.6.pptx)
- [templates/组会ppt6.20.pptx](templates/组会ppt6.20.pptx)

## 组会总结结构

1. 上次组会以来的进展。
2. 证据和结果。
3. 问题和风险。
4. 未来两周计划。

## 幻灯片结构

1. 研究目标和当前论文主线。
2. 相比上次组会的变化。
3. 实验结果和关键表格。
4. 结果解读：支持什么、不支持什么。
5. 问题和未来两周计划。

## 下一次组会建议内容

建议重点：

- Exp0 已经在 ScienceQA 上成功跑通。
- 图像缺失与 subject/topic/skill 存在结构关联。
- 当前报告中，skill 几乎可以完美预测 `has_image`。
- Exp0.1 人工复核区分了 `structural_absence` 和需要图但缺图的 `accidental_missing`；最终没有样本保留为 `ambiguous`。
