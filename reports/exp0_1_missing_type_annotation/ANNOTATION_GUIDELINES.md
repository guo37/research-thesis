# 缺失类型标注指南

## 目标

判断一个无图 ScienceQA 题目是缺少有教学价值的视觉模态，还是本身就是自然的纯文本题目。

## 标签

| 标签 | 定义 | 判断规则 |
| --- | --- | --- |
| `observed` | 原始题目有图像。 | 用于 `has_image=1` 的参考样本。 |
| `structural_absence` | 题目不依赖图像即可理解和求解，教学上不需要图。 | 题目主要涉及语言、定义、抽象推理、事实回忆或纯文本证据。 |
| `accidental_missing` | 题目通常需要或明显受益于视觉信息，但该记录中没有图。 | 题目涉及地图、图表、图形、物体属性、空间布局或视觉比较，但 `has_image=0`。 |
| `ambiguous` | 是否需要图像无法明确判断。 | 当图像可能有帮助，但文本也包含足够信息，或题目表述不充分时使用。 |

## 重要规则

不要自动把 `suggested_missing_type` 复制到 `human_label`。它只是基于 topic/skill 缺失率统计得到的抽样提示。

## 推荐标注流程

1. 阅读 `question`、`choices`、`hint`、`lecture` 和 `solution`。
2. 检查 `has_image`。
3. 如果 `has_image=1`，除非该行明显异常，否则标为 `observed`。
4. 如果 `has_image=0`，判断图像是否具有教学必要性。
5. 在 `label_confidence` 中填写 `high`、`medium` 或 `low`。
6. 在 `label_note` 中写简短证据，尤其是在不同意 `suggested_missing_type` 时。

## 示例

- 明喻/隐喻、标点、语法：通常是 `structural_absence`。
- 地图阅读、地理位置、图像比较：如果 `has_image=0`，通常是 `accidental_missing`。
- 生物分类或物理属性：需要看具体题目；文本可能足够，但图像也可能明显有帮助。
