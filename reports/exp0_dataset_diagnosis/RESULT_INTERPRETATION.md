# Exp0 ScienceQA 数据诊断结果解读

生成日期：2026-06-17

## 1. 实验是否跑通

已跑通正式 ScienceQA 数据诊断。

- 样本总数：21,208
- train / validation / test：12,726 / 4,241 / 4,241
- 有图样本：10,332，占 48.72%
- 无图样本：10,876，占 51.28%

本轮只标记 `has_image = 1 / 0`，没有把无图样本直接标成 `structural_absence`。

## 2. 描述性结论

ScienceQA 的图像缺失不是均匀分布的。

subject 层面已经有明显差异：

| subject | n | missing_rate |
| --- | ---: | ---: |
| language science | 5,371 | 95.75% |
| natural science | 11,487 | 44.88% |
| social science | 4,350 | 13.29% |

topic 层面的差异更明显。一些 topic 几乎全无图：

| topic | n | missing_rate |
| --- | ---: | ---: |
| figurative-language | 1,260 | 100.00% |
| units-and-measurement | 870 | 100.00% |
| reference-skills | 724 | 100.00% |
| punctuation | 514 | 100.00% |
| grammar | 379 | 100.00% |
| writing-strategies | 1,650 | 91.58% |

也有一些 topic 几乎都有图：

| topic | n | missing_rate |
| --- | ---: | ---: |
| geography | 2,956 | 0.41% |
| us-history | 510 | 8.43% |
| literacy-in-science | 34 | 14.71% |
| world-history | 65 | 18.46% |

这说明 ScienceQA 中图像是否存在与学科、主题、技能有强结构关联。

## 3. 统计检验结论

mutual information：

| field | mutual_information |
| --- | ---: |
| subject | 0.2505 |
| topic | 0.3211 |
| skill | 0.6884 |
| grade | 0.0719 |

skill 的互信息最高，说明它对 `has_image` 的解释力最强。topic 也高于 subject，说明缺图机制不只是粗粒度学科差异。

chi-square test 全部显著：

| field | chi2 | p_value |
| --- | ---: | ---: |
| subject | 6954.1395 | < 0.0001 |
| topic | 9745.0370 | < 0.0001 |
| skill | 20933.3005 | < 0.0001 |
| grade | 2275.1555 | < 0.0001 |

这支持“图像缺失与 metadata 变量不独立”的判断。

## 4. 预测性结论

test split 上的 AUC：

| model | test AUC |
| --- | ---: |
| majority | 0.5000 |
| subject_only | 0.7985 |
| topic_only | 0.8833 |
| skill_only | 0.9997 |
| topic_skill | 0.9997 |
| subject_topic_skill | 0.9996 |
| full_metadata_text | 0.9997 |

关键判断：

1. subject-only 明显优于 majority，说明缺图机制不是随机的。
2. topic-only 明显优于 subject-only，说明 topic 提供了超过 subject 的细粒度解释力。
3. skill-only 几乎完美预测 `has_image`，说明 ScienceQA 的图像存在与 skill 强绑定。
4. full model 没有明显超过 skill-only，说明主要信号已经被 skill 捕获。

因此，RC2 的第一阶段判断是：

> ScienceQA 支持 structured missingness / MNAR 的初步假设，尤其支持 skill-dependent missingness。

## 5. 对论文主线的意义

这个结果支持继续推进 RC2，但表述要谨慎。

可以说：

> ScienceQA 中图像缺失具有明显的 subject/topic/skill 依赖性，特别是 skill 对图像存在具有极强预测力。这说明教育多模态资源中的缺失模态不能简单视为随机缺失，也不能默认全部需要补全。

暂时不要说：

> 所有无图样本都是 structural absence。

原因是 `has_image = 0` 只说明数据中没有图，不说明这道题教学上不需要图。下一步必须做 missing type 小规模标注。

## 6. 下一步建议

建议进入 Exp0.1：missing type annotation candidate construction。

目标：

1. 从 high-missing topic/skill 中抽取 structural_absence 候选。
2. 从 low-missing topic/skill 中抽取无图样本作为 accidental_missing 候选。
3. 构建 300-500 条人工标注表。
4. 字段包括：resource_id、question、choices、subject、topic、skill、has_image、candidate_reason、suggested_missing_type、human_label、label_note。

优先抽样策略：

- high missing-rate topic 且 has_image = 0：候选 `structural_absence`
- low missing-rate topic 且 has_image = 0：候选 `accidental_missing`
- 中间 missing-rate topic：候选 `ambiguous`

当前结果已经足够支持 RC2 继续作为 `MNAR-aware selective completion` 推进。
