"""分析 Exp0.1 缺失类型标签，并生成 Markdown 报告。"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Iterable


LABELS = ["observed", "structural_absence", "accidental_missing", "ambiguous"]
MISSING_LABELS = ["structural_absence", "accidental_missing", "ambiguous"]


def pct(count: int, total: int) -> str:
    if total <= 0:
        return "0.0%"
    return f"{count / total * 100:.1f}%"


def md_table(headers: list[str], rows: Iterable[Iterable[object]]) -> str:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        out.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(out)


def count_by(rows: list[dict[str, str]], field: str) -> Counter[str]:
    return Counter((row.get(field) or "").strip() for row in rows)


def label_rows(counter: Counter[str], total: int) -> list[list[object]]:
    return [[label, counter.get(label, 0), pct(counter.get(label, 0), total)] for label in LABELS]


def crosstab(rows: list[dict[str, str]], group_field: str, labels: list[str] = LABELS) -> list[list[object]]:
    groups = count_by(rows, group_field)
    table = []
    for group, total in groups.most_common():
        group_rows = [row for row in rows if (row.get(group_field) or "").strip() == group]
        counts = count_by(group_rows, "human_label")
        table.append([group or "<blank>", total, *[counts.get(label, 0) for label in labels]])
    return table


def confidence_band(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return "<blank>"
    try:
        score = float(text)
    except ValueError:
        return "invalid"
    if score >= 0.90:
        return ">=0.90"
    if score >= 0.80:
        return "0.80-0.89"
    if score >= 0.70:
        return "0.70-0.79"
    return "<0.70"


def consistency_issues(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    issues = []
    for row in rows:
        label = (row.get("human_label") or "").strip()
        has_image = (row.get("has_image") or "").strip()
        if label == "observed" and has_image != "1":
            issues.append(row)
        if label in {"structural_absence", "accidental_missing"} and has_image != "0":
            issues.append(row)
    return issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="data/scienceqa/annotation/missing_type_annotation_candidates.csv",
        help="已标注的 Exp0.1 候选 CSV。",
    )
    parser.add_argument(
        "--output",
        default="reports/exp0_1_missing_type_annotation/human_label_analysis.md",
        help="Markdown 报告路径。",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    missing_rows = [row for row in rows if (row.get("has_image") or "").strip() == "0"]
    label_counts = count_by(rows, "human_label")
    missing_label_counts = count_by(missing_rows, "human_label")
    invalid_labels = sorted(label for label in label_counts if label and label not in LABELS)
    blank_labels = label_counts.get("", 0)
    issues = consistency_issues(rows)

    confidence_counts = Counter(confidence_band(row.get("label_confidence", "")) for row in rows)
    confidence_rows = [[band, confidence_counts.get(band, 0)] for band in [">=0.90", "0.80-0.89", "0.70-0.79", "<0.70", "<blank>", "invalid"]]

    top_topics = []
    for topic, count in count_by(rows, "topic").most_common(15):
        topic_rows = [row for row in rows if (row.get("topic") or "").strip() == topic]
        labels = count_by(topic_rows, "human_label")
        top_topics.append([topic, count, *[labels.get(label, 0) for label in LABELS]])

    suggested_rows = crosstab(rows, "suggested_missing_type")
    subject_rows = crosstab(rows, "subject")
    split_rows = crosstab(rows, "split")

    non_observed_missing = missing_label_counts.get("accidental_missing", 0) + missing_label_counts.get("ambiguous", 0)
    structural_missing = missing_label_counts.get("structural_absence", 0)
    accidental_missing = missing_label_counts.get("accidental_missing", 0)
    ambiguous_missing = missing_label_counts.get("ambiguous", 0)
    if ambiguous_missing == 0:
        interpretation_lines = [
            f"- 在缺图样本中，`{structural_missing}` / `{len(missing_rows)}`（{pct(structural_missing, len(missing_rows))}）被标为 `structural_absence`。",
            f"- 在缺图样本中，`{accidental_missing}` / `{len(missing_rows)}`（{pct(accidental_missing, len(missing_rows))}）被标为 `accidental_missing`：这些题目需要图，但数据中缺图。",
            "- 人工复核后，没有样本继续保留为 `ambiguous`。",
            "- 下一步 RC2 任务应是二分类模态必要性门控：在缺图样本中预测 `structural_absence` vs `accidental_missing`。",
            "- 正类样本集中在 natural-science/biology，因此论文使用前应进行 topic/skill 分组测试。",
        ]
        target_definition = "`accidental_missing`"
    else:
        interpretation_lines = [
            f"- 在缺图样本中，`{structural_missing}` / `{len(missing_rows)}`（{pct(structural_missing, len(missing_rows))}）被标为 `structural_absence`。",
            f"- 在缺图样本中，`{non_observed_missing}` / `{len(missing_rows)}`（{pct(non_observed_missing, len(missing_rows))}）为 `ambiguous` 或 `accidental_missing`，应作为复核/补全候选，而不是自动补全。",
            "- 下一步 RC2 任务应是选择性补全门控：在缺图样本中预测 `structural_absence` vs `review_or_completion_needed`。",
            "- 不确定样本集中在 natural-science/biology，说明门控模型需要结合 topic/skill 和题目文本，而不能只依赖 subject。",
        ]
        target_definition = "`accidental_missing OR ambiguous`"

    lines = [
        "# Exp0.1 人工标签分析",
        "",
        "基于 `data/scienceqa/annotation/missing_type_annotation_candidates.csv` 生成。",
        "",
        "## 数据质量",
        "",
        md_table(
            ["检查项", "值"],
            [
                ["总行数", total],
                ["缺图样本数", len(missing_rows)],
                ["空白 `human_label`", blank_labels],
                ["非法标签", ", ".join(invalid_labels) if invalid_labels else "0"],
                ["图像状态/标签一致性问题", len(issues)],
            ],
        ),
        "",
        "## 标签分布",
        "",
        md_table(["标签", "数量", "占全部样本比例"], label_rows(label_counts, total)),
        "",
        "只看缺图样本：",
        "",
        md_table(
            ["标签", "数量", "占缺图样本比例"],
            [[label, missing_label_counts.get(label, 0), pct(missing_label_counts.get(label, 0), len(missing_rows))] for label in MISSING_LABELS],
        ),
        "",
        "## 抽样提示类型 vs 人工标签",
        "",
        md_table(["抽样提示类型", "总数", *LABELS], suggested_rows),
        "",
        "## Subject vs 人工标签",
        "",
        md_table(["Subject", "总数", *LABELS], subject_rows),
        "",
        "## 数据划分 vs 人工标签",
        "",
        md_table(["数据划分", "总数", *LABELS], split_rows),
        "",
        "## 主要 Topic",
        "",
        md_table(["Topic", "总数", *LABELS], top_topics),
        "",
        "## 置信度分布",
        "",
        md_table(["置信度区间", "数量"], confidence_rows),
        "",
        "## 结果解读",
        "",
        *interpretation_lines,
        "",
        "## 推荐下一步实验",
        "",
        f"在缺图样本中，将正类定义为 {target_definition}。",
        "",
        "运行 Exp0.2 基线对比：",
        "",
        "1. 多数类基线。",
        "2. 仅元数据 Logistic Regression：subject、topic、skill、grade、text length。",
        "3. 仅文本 TF-IDF Logistic Regression：question、choices、hint、lecture、solution。",
        "4. 元数据 + 文本 TF-IDF Logistic Regression。",
        "",
        "报告 balanced accuracy、macro F1、正类 F1、PR-AUC 和混淆矩阵。",
        "",
        "如果 Exp0.2 能明显优于基线地识别“需要图但缺图”的样本，RC2 可以继续按 `MNAR-aware selective completion` 推进。否则，RC2 应收窄为描述性 MNAR 诊断和规则辅助的模态必要性分析。",
        "",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
