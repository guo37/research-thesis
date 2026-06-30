# 面向教育资源检索的可信多模态知识推理研究：最终主线与实施方案

版本：v1.0  
日期：2026-06-17  
用途：作为后续硕士论文写作、实验设计和代码实现的主线文档。  

---

## 0. 重要结论：以新版主线为准

当前研究材料中存在两条路线：

1. 旧路线：  
   **基于图基础模型与因果推理的教育多模态知识图谱补全及可解释推荐方法研究**

2. 新路线：  
   **面向教育资源检索的可信多模态知识推理研究**

后续论文应以新路线为准。旧路线中的 GFM 预训练、Causal VAE 补全、LLM prompt 解释等内容，只能作为 **pilot / preliminary results**，用于说明前期探索过程，不应作为最终主实验和核心贡献。

最终研究主旨：

> 面向教育资源检索场景，围绕“资源是否对齐、缺失是否可信、解释是否忠实”三个核心问题，研究教育知识结构约束的跨模态对齐、非随机模态缺失下的选择性补全，以及融合路径、对齐与模态可靠性的图约束解释生成方法。

---

## 1. 推荐论文题目

中文题目：

> 面向教育资源检索的可信多模态知识推理研究

英文题目：

> Trustworthy Multimodal Knowledge Reasoning for Educational Resource Retrieval

不建议继续使用：

> 基于图基础模型与因果推理的教育多模态知识图谱补全及可解释推荐方法研究

原因：

1. “图基础模型”概念过大，若只使用 GraphSAGE、adapter 或若干预训练 loss，容易被质疑不是真正的 Graph Foundation Model。
2. “知识图谱补全”容易把研究引向传统 KG completion，而实际任务是教育资源检索、跨模态对齐、缺失可靠性建模和解释生成。
3. “Causal VAE 补全”如果只报告 CosSim，学术支撑不足。
4. “LLM 解释”如果只做 prompt，创新性和评估强度不足。

---

## 2. 总体科学问题

教育资源检索不是单纯的文本检索，也不是普通图文匹配。它需要回答三个可信问题：

| 问题      | 对应研究内容                    | 核心输出                                |
| ------- | ------------------------- | ----------------------------------- |
| 资源是否对齐？ | RC1：教育知识结构约束的跨模态资源对齐      | alignment score                     |
| 缺失是否可信？ | RC2：面向非随机模态缺失的选择性补全       | modality status / reliability score |
| 解释是否忠实？ | RC3：融合路径、对齐与模态可靠性的图约束解释生成 | faithful explanation                |

三者关系：

```text
RC1：跨模态资源对齐
    输出：resource-concept alignment score
        ↓
RC2：缺失模态可靠性建模
    输出：modality status + reliability score
        ↓
RC3：图约束解释生成
    输入：alignment score + reliability score + graph path
    输出：可验证、可追溯、教学可操作的解释
```

注意：三个研究内容不是一个强行拼接的大一统模型，而是围绕教育资源检索可信性展开的三个递进科学问题。

---

## 3. 最终论文贡献表述

建议最终贡献写成四点：

### Contribution 1：教育知识结构约束的跨模态资源对齐

针对通用视觉-语言模型在教育资源检索中存在概念粒度错配的问题，提出教育知识结构约束的跨模态资源对齐方法。该方法通过 concept-aware hard negatives、resource-concept alignment 和 hierarchy-aware regularization，使模型不仅学习图文语义相似性，还学习资源与知识点、认知粒度和教学目标之间的一致性。

### Contribution 2：面向非随机模态缺失的选择性补全

针对教育资源中图像模态缺失并非随机发生的问题，提出 MNAR-aware 选择性补全框架。该框架首先建模缺失机制，区分 accidental missing、structural absence 和 ambiguous missing，再仅对确有视觉需求的偶然缺失资源进行补全或替代检索，避免对结构性无图资源进行不必要甚至有害的视觉补全。

### Contribution 3：融合路径、对齐与模态可靠性的图约束解释生成

针对 LLM 推荐解释容易产生无依据陈述和图谱外幻觉的问题，提出路径-对齐-可靠性融合的解释生成框架。该框架将知识路径、资源-概念对齐得分、模态状态和可靠性得分组织为 evidence package，并通过 verifier 检查解释中的实体、关系和资源声明是否被证据支持。

### Contribution 4：面向教育资源检索的可信评测协议

构建覆盖跨模态检索、缺失模态鲁棒性和解释忠实性的多维评测协议，包括 Recall@K、MRR、missingness AUC、structural absence detection、path faithfulness、entity grounding、unsupported claim rate 和 hallucination rate 等指标。

---

## 4. 旧实验结果的处理方式

旧实验材料不可直接作为最终主实验。建议统一处理为：

> Preliminary exploration / pilot study

具体降级方式：

| 旧内容                     | 处理方式                                                                          |
| ----------------------- | ----------------------------------------------------------------------------- |
| GraphSAGE + 多任务 GFM 预训练 | 作为前期探索，说明直接 message passing 可能污染跨模态对齐空间                                       |
| CMA 对齐实验                | 可保留为 pilot，提示 adapter + contrastive learning 有效果，但需要补齐 hard-negative baseline |
| Causal VAE CosSim 补全    | 可保留为补全模型探索，但不能作为 RC2 核心结论                                                     |
| LLM prompt 解释样例         | 可保留为 demo，不作为 RC3 实验结果                                                        |
| 原 `PAPER_OUTLINE.md`    | 作为旧版本归档，不建议继续作为论文主线                                                           |

最终论文中如果需要引用旧实验，应写成：

> 前期探索表明，简单将图消息传递引入跨模态空间可能造成负迁移，因此本文后续将教育知识结构主要用于 hard negative 构造、层级约束和解释路径，而非直接进行无约束图卷积传播。

---

## 5. 研究内容一：教育知识结构约束的跨模态资源对齐方法

### 5.1 科学问题

通用 CLIP / BLIP / SigLIP 学习的是开放域图文匹配，但教育资源检索更关心：

> 资源是否对应同一个知识点、认知粒度和教学目标？

核心科学问题：

> 教育知识结构能否缓解通用视觉-语言模型在教育资源检索中的概念粒度错配？

进一步拆分：

1. 通用 CLIP 在 ScienceQA 等教育数据上是否会混淆同学科相近知识点？
2. concept-aware hard negative 是否优于 random negative？
3. hierarchy regularization 是否能提升 concept-level retrieval？
4. 图结构更适合作为 hard-negative sampler / regularization，还是 message passing？

### 5.2 方法定位

不要写成：

> 基于图基础模型的跨模态对齐

应写成：

> 教育知识结构约束的跨模态资源对齐方法

推荐方法名：

> CS-CMA: Concept-Structure-Aware Cross-Modal Alignment

### 5.3 技术路线

```text
ScienceQA resource:
    question / lecture / image / subject / topic / skill
        ↓
Frozen CLIP / SigLIP encoder
        ↓
modality-specific adapter
        ↓
shared educational semantic space
        ↓
concept-aware training:
    L_itc: image-text contrastive loss
    L_rc: resource-concept alignment loss
    L_hn: hard-negative contrastive loss
    L_hierarchy: hierarchy-aware regularization
        ↓
resource-concept alignment score
```

### 5.4 Hard negative 设计

教育资源检索中，真正困难的负样本不是随机负样本，而是：

| 类型                         | 示例                                  | 意义   |
| -------------------------- | ----------------------------------- | ---- |
| random negative            | physics query vs grammar image      | 太容易  |
| same-subject negative      | physics query vs biology image      | 中等难度 |
| same-topic different skill | force query vs acceleration image   | 高难度  |
| adjacent-concept negative  | acceleration vs Newton's second law | 最关键  |

### 5.5 Baseline

必须包含：

1. CLIP zero-shot retrieval
2. SigLIP / BLIP 可选 baseline
3. CLIP + linear adapter
4. ordinary contrastive fine-tuning
5. random hard negative
6. same-subject hard negative
7. concept-aware hard negative
8. concept-aware hard negative + hierarchy loss
9. message passing variant（作为图结构是否有害的对照）

### 5.6 指标

| 指标                               | 目的            |
| -------------------------------- | ------------- |
| Recall@1/5/10                    | 基础检索性能        |
| MRR                              | 排序质量          |
| Concept-level retrieval accuracy | 是否检索到同知识点资源   |
| Same-subject confusion rate      | 是否混淆近邻知识点     |
| Hard-negative error rate         | 是否能区分教学目标相近资源 |
| Modality gap                     | 对齐空间诊断        |

### 5.7 论文论点

不能只写：

> 本方法提升 R@K。

必须写：

> 本方法通过教育知识结构构造高质量 hard negatives，使跨模态对齐从“开放域语义相似”转向“教学目标一致”。

---

## 6. 研究内容二：面向非随机模态缺失的选择性补全方法

### 6.1 科学问题

教育资源中的图像缺失不一定是错误：

- 语法题没有图，可能是正常的结构性无图；
- 几何题没有图，可能是严重的偶然缺失；
- 历史题是否需要图，要看具体知识点。

核心科学问题：

> 教育多模态资源中的模态缺失是否具有知识点依赖的 structured missingness / MNAR 特征？如果有，如何选择性补全以避免教育幻觉？

### 6.2 RC2 为什么最有创新潜力

RC2 最有辨识度，因为它把问题从：

> 如何补全缺失图像？

改成：

> 哪些缺失应该补，哪些缺失不应该补？

这是教育场景区别于普通 missing modality 任务的关键。

### 6.3 技术路线

推荐方法名：

> MAS-MC: MNAR-Aware Selective Modality Completion

流程：

```text
resource metadata:
    subject / topic / skill / grade / text
        ↓
Missingness mechanism diagnosis:
    P(has_image | subject, topic, skill, grade, text_length)
        ↓
Missing type classifier:
    observed
    accidental_missing
    structural_absence
    ambiguous
        ↓
Selective completion:
    if accidental_missing:
        retrieve / generate visual substitute
    if structural_absence:
        no visual completion; use text-only reliable representation
    if ambiguous:
        low-confidence fallback
        ↓
modality status + reliability score
```

### 6.4 必须先做的数据诊断

RC2 的第一步不是训练补全模型，而是证明 missingness 不是随机的。

实验：

```text
has_image ~ subject + topic + skill + grade + text_length
```

报告：

1. topic-level missing rate
2. skill-level missing rate
3. subject-level missing rate
4. mutual information: I(topic; has_image)
5. chi-square test
6. logistic regression AUC

判断标准：

> 如果 topic / skill 能显著预测 has_image，则支持 structured missingness / MNAR 假设。

### 6.5 缺失类型标注集

需要构建 300-500 条小规模标注集。

标签：

| 标签                 | 含义           |
| ------------------ | ------------ |
| observed           | 原始有图         |
| accidental_missing | 理论上需要图，但数据缺图 |
| structural_absence | 该资源本身不需要图    |
| ambiguous          | 是否需要图不确定     |

标注流程：

1. 规则预标：
   - high missing-rate topic → structural_absence 候选
   - low missing-rate topic 中无图样本 → accidental_missing 候选
2. LLM 辅助判断：
   - “这道题是否需要图像才能更好理解？”
3. 人工抽检修正。

### 6.6 Baseline

必须包含：

1. no completion
2. zero / mean imputation
3. vanilla VAE / conditional VAE
4. modality dropout robust fusion
5. dynamic modality expert
6. causal imputation without selective gate
7. selective completion（完整方法）

### 6.7 指标

#### 缺失机制指标

- AUC
- F1
- mutual information
- chi-square

#### 缺失类型指标

- structural absence precision
- accidental missing recall
- missing type macro-F1

#### 下游检索指标

- missing condition Recall@K
- robustness under image dropout
- high-MNAR group performance
- hallucinated visual completion rate

### 6.8 论文论点

不要写：

> 我们提升了图像补全 CosSim。

应写：

> 我们证明教育资源图像缺失具有知识点依赖的结构化特征，并通过选择性补全避免对结构性无图资源进行不必要补全，从而提升缺失条件下资源检索的可靠性。

---

## 7. 研究内容三：融合路径、对齐与模态可靠性的图约束解释生成方法

### 7.1 科学问题

LLM 可以生成流畅解释，但教育推荐解释必须回答：

1. 为什么推荐这条路径？
2. 这些资源是否和目标知识点对齐？
3. 这些资源的模态是否完整、可靠？
4. 解释中的概念和关系是否真实存在？

核心科学问题：

> 如何让教育资源推荐解释同时具备知识路径忠实性、跨模态证据一致性和教学可操作性？

### 7.2 方法定位

不要写成：

> LLM prompt 解释生成

应写成：

> 融合路径、对齐与模态可靠性的图约束解释生成

推荐方法名：

> PAR-GE: Path-Alignment-Reliability Grounded Explanation

### 7.3 技术路线

```text
student query / target concept / current concept
        ↓
concept identification
        ↓
path retrieval:
    prerequisite / related / remedial path
        ↓
resource retrieval:
    retrieve resources for path concepts
        ↓
evidence package:
    graph path
    alignment score from RC1
    modality status from RC2
    reliability score
        ↓
constrained LLM explanation
        ↓
verifier:
    entity grounding
    relation grounding
    unsupported claim detection
        ↓
faithful educational explanation
```

### 7.4 Evidence package

每条解释输入应包含：

```json
{
  "student_query": "...",
  "target_concept": "...",
  "path": [
    {
      "source": "force",
      "relation": "prerequisite_of",
      "target": "acceleration"
    }
  ],
  "resources": [
    {
      "resource_id": "r001",
      "concept": "acceleration",
      "alignment_score": 0.82,
      "modality_status": "original_multimodal",
      "reliability_score": 0.91
    }
  ]
}
```

### 7.5 数据构造

ScienceQA 没有显式 prerequisite relation，因此 RC3 必须额外构图。

建议：

1. 不构建复杂大图。
2. 先构建 100-300 条高质量解释评测集。
3. 关系类型限制为：
   - prerequisite_of
   - related_to
   - remedial_for
   - belongs_to
4. 路径来源：
   - 小规模人工 prerequisite graph；
   - LLM 辅助生成 + 人工抽检；
   - subject-topic-skill hierarchy 作为弱路径。

### 7.6 Baseline

必须包含：

1. LLM-only explanation
2. RAG explanation
3. KG-path prompt
4. Path + alignment
5. Path + reliability
6. Full：Path + alignment + reliability + verifier

### 7.7 指标

自动指标：

| 指标                      | 含义                |
| ----------------------- | ----------------- |
| Entity grounding rate   | 解释中的概念/资源是否存在于证据包 |
| Relation grounding rate | 解释中的关系是否存在于图谱     |
| Path faithfulness       | 解释是否忠实于路径         |
| Unsupported claim rate  | 无证据支持的陈述比例        |
| Evidence coverage       | 是否覆盖关键路径节点和资源证据   |
| Hallucination rate      | 图谱外实体或资源比例        |

人工指标：

- 教学合理性
- 个性化程度
- 可操作性
- 可信度
- 解释清晰度

### 7.8 论文论点

不要写：

> LLM 可以生成解释。

应写：

> 路径、对齐证据和模态可靠性共同构成可验证 evidence package，可降低 LLM 教育推荐解释中的无依据陈述和图谱外幻觉。

---

## 8. 数据集与统一 schema

### 8.1 主数据集：ScienceQA

ScienceQA 可作为主数据集，但必须明确：

> ScienceQA 是多模态科学问答数据集，本研究将其重构为教育资源检索实验数据，而不是直接把它当作完整知识图谱。

可用字段：

```text
image
question
choices
answer
hint
task
grade
subject
topic
category
skill
lecture
solution
```

### 8.2 统一 schema

建议构建：

```text
resources.csv
concepts.csv
resource_concept_edges.csv
concept_edges.csv
modality_status.csv
```

这些表构成三章共享的数据底座。

### 8.3 备用数据

| 数据                 | 作用                      | 当前定位                       |
| ------------------ | ----------------------- | -------------------------- |
| MOOCCube / MOOCRep | 课程-概念-视频图谱              | 备用或扩展实验                    |
| OpenStax / 教材目录    | 构建高质量 concept hierarchy | 可用于 RC3 prerequisite graph |
| 自建小规模图谱            | 控制路径质量                  | RC3 推荐                     |

---

## 9. 最终论文结构

### 第 1 章 绪论

核心：

1. 教育资源检索需要可信多模态知识推理。
2. 三个问题：资源是否对齐、缺失是否可信、解释是否忠实。
3. 本文贡献。

### 第 2 章 相关工作

按科学问题组织：

2.1 教育资源跨模态对齐  
2.2 缺失模态学习与结构化缺失  
2.3 KG-grounded LLM 与解释忠实性  

不要按“GFM、Causal VAE、LLM”机械堆技术。

### 第 3 章 教育知识结构约束的跨模态资源对齐方法

核心：

- concept-aware hard negative；
- resource-concept alignment；
- hierarchy regularization；
- 证明教育结构约束比 ordinary contrastive 更有效。

### 第 4 章 面向非随机模态缺失的选择性补全方法

核心：

- missingness diagnosis；
- missing type annotation；
- selective completion；
- 证明不是所有缺失都应补全。

### 第 5 章 融合路径、对齐与模态可靠性的图约束解释生成方法

核心：

- evidence package；
- LLM constrained explanation；
- verifier；
- faithfulness evaluation。

### 第 6 章 总结与展望

总结三个可信问题的解决思路、局限和未来工作。

---

## 10. 优先修改清单

### P0：立即执行

1. 统一题目与贡献表述。
2. 将 `PAPER_OUTLINE.md` 中旧实验标注为 preliminary。
3. 优先跑 RC2 数据诊断。
4. 建立 ScienceQA 统一 schema。

### P1：下一阶段

1. RC1 补齐 ordinary contrastive、random hard negative、same-subject hard negative baseline。
2. RC2 构建 300-500 条 missing type 标注集。
3. RC3 构建 100-300 条解释评测集。

### P2：论文写作

1. Related Work 扩展到 30-40 篇。
2. 每个研究内容对应 10-12 篇核心论文。
3. 所有实验必须对齐科学问题。

---

## 11. 下一步最小执行计划

### Step 1：ScienceQA 数据诊断

输出：

```text
resources.csv
concepts.csv
resource_concept_edges.csv
concept_edges.csv
modality_status.csv
dataset_statistics.md
```

目标：

> 证明 image missingness 是否依赖 topic / skill。

### Step 2：RC2 MNAR 验证

实验：

```text
has_image ~ subject + topic + skill + grade + text_length
```

如果 AUC 明显高于 majority baseline，RC2 继续推进。  
如果不明显，RC2 需要调整为一般 missing modality robustness。

### Step 3：RC1 对齐实验

先做：

```text
CLIP
CLIP + adapter
ordinary contrastive
random hard negative
same-subject hard negative
concept-aware hard negative
```

### Step 4：RC3 解释评测集

先构建 100 条样本：

```text
query
target_concept
path
candidate_resources
alignment_score
modality_status
reference evidence
```

---

## 12. 最终判断

这条新主线可以支撑一篇完整硕士论文，但必须避免“概念堆太大、实验支撑不够”的风险。

最值得保留的核心创新是：

> 教育知识结构约束跨模态对齐 + MNAR-aware 选择性补全 + 路径/对齐/可靠性约束解释生成。

最终论文的关键不是证明“我用了 GFM / Causal VAE / LLM”，而是证明：

1. 教育知识结构能让跨模态资源检索更符合教学目标；
2. 教育资源中的图像缺失具有结构化特征，不能盲目补全；
3. 路径、对齐与可靠性证据能让 LLM 解释更忠实、更可信。
