"""Analyze Exp0.1 missing-type labels and write a Markdown report."""

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
        help="Annotated Exp0.1 candidate CSV.",
    )
    parser.add_argument(
        "--output",
        default="reports/exp0_1_missing_type_annotation/human_label_analysis.md",
        help="Markdown report path.",
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
            f"- Among missing-image rows, `{structural_missing}` / `{len(missing_rows)}` ({pct(structural_missing, len(missing_rows))}) are labeled `structural_absence`.",
            f"- Among missing-image rows, `{accidental_missing}` / `{len(missing_rows)}` ({pct(accidental_missing, len(missing_rows))}) are labeled `accidental_missing`: these are items where an image is needed but absent.",
            "- No rows remain labeled `ambiguous` after manual review.",
            "- The next RC2 task should be a binary modality-necessity gate: predict `structural_absence` vs `accidental_missing` for missing-image samples.",
            "- Positive labels are concentrated in natural-science/biology rows, so the gate should be tested with topic/skill grouped splits before thesis use.",
        ]
        target_definition = "`accidental_missing`"
    else:
        interpretation_lines = [
            f"- Among missing-image rows, `{structural_missing}` / `{len(missing_rows)}` ({pct(structural_missing, len(missing_rows))}) are labeled `structural_absence`.",
            f"- Among missing-image rows, `{non_observed_missing}` / `{len(missing_rows)}` ({pct(non_observed_missing, len(missing_rows))}) are `ambiguous` or `accidental_missing`, so they should be treated as review/completion candidates rather than automatically completed.",
            "- The next RC2 task should be a selective-completion gate: predict `structural_absence` vs `review_or_completion_needed` for missing-image samples.",
            "- Ambiguity is concentrated in natural-science/biology rows, which suggests the gate should use topic/skill plus question text rather than subject alone.",
        ]
        target_definition = "`accidental_missing OR ambiguous`"

    lines = [
        "# Exp0.1 Human Label Analysis",
        "",
        "Generated from `data/scienceqa/annotation/missing_type_annotation_candidates.csv`.",
        "",
        "## Data Quality",
        "",
        md_table(
            ["Check", "Value"],
            [
                ["Total rows", total],
                ["Missing-image rows", len(missing_rows)],
                ["Blank `human_label`", blank_labels],
                ["Invalid labels", ", ".join(invalid_labels) if invalid_labels else "0"],
                ["Image/label consistency issues", len(issues)],
            ],
        ),
        "",
        "## Label Distribution",
        "",
        md_table(["Label", "Count", "Share of all rows"], label_rows(label_counts, total)),
        "",
        "Missing-image rows only:",
        "",
        md_table(
            ["Label", "Count", "Share of missing-image rows"],
            [[label, missing_label_counts.get(label, 0), pct(missing_label_counts.get(label, 0), len(missing_rows))] for label in MISSING_LABELS],
        ),
        "",
        "## Suggested Type vs Human Label",
        "",
        md_table(["Suggested type", "Total", *LABELS], suggested_rows),
        "",
        "## Subject vs Human Label",
        "",
        md_table(["Subject", "Total", *LABELS], subject_rows),
        "",
        "## Split vs Human Label",
        "",
        md_table(["Split", "Total", *LABELS], split_rows),
        "",
        "## Top Topics",
        "",
        md_table(["Topic", "Total", *LABELS], top_topics),
        "",
        "## Confidence Distribution",
        "",
        md_table(["Confidence band", "Count"], confidence_rows),
        "",
        "## Interpretation",
        "",
        *interpretation_lines,
        "",
        "## Recommended Next Experiment",
        "",
        f"Define the positive class as {target_definition} for missing-image rows.",
        "",
        "Run an Exp0.2 baseline comparison:",
        "",
        "1. Majority baseline.",
        "2. Metadata-only logistic regression: subject, topic, skill, grade, text length.",
        "3. Text-only TF-IDF logistic regression: question, choices, hint, lecture, solution.",
        "4. Metadata + text TF-IDF logistic regression.",
        "",
        "Report balanced accuracy, macro F1, positive-class F1, PR-AUC, and confusion matrix.",
        "",
        "If Exp0.2 can identify image-needed missing samples above baseline, RC2 can continue as `MNAR-aware selective completion`. If not, RC2 should be narrowed to descriptive MNAR diagnosis plus rule-assisted modality necessity analysis.",
        "",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
