"""构建 Exp0.1 缺失类型标注候选集。

该脚本在 Exp0 后生成 300-500 条人工标注候选样本。
它不分配最终缺失类型，只提供候选抽样。
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


DEFAULT_CONFIG = {
    "paths": {
        "resources_csv": "data/scienceqa/processed/resources.csv",
        "topic_stats_csv": "reports/exp0_dataset_diagnosis/missingness_by_topic.csv",
        "skill_stats_csv": "reports/exp0_dataset_diagnosis/missingness_by_skill.csv",
        "output_dir": "data/scienceqa/annotation",
        "report_dir": "reports/exp0_1_missing_type_annotation",
    },
    "sampling": {
        "random_seed": 42,
        "total_candidates": 450,
        "structural_absence_candidates": 150,
        "accidental_missing_candidates": 150,
        "ambiguous_missing_candidates": 100,
        "observed_reference_candidates": 50,
    },
    "thresholds": {
        "min_group_count": 20,
        "high_missing_rate": 0.90,
        "low_missing_rate": 0.20,
        "ambiguous_low": 0.35,
        "ambiguous_high": 0.65,
    },
}


@dataclass
class Config:
    resources_csv: Path
    topic_stats_csv: Path
    skill_stats_csv: Path
    output_dir: Path
    report_dir: Path
    random_seed: int
    total_candidates: int
    n_structural: int
    n_accidental: int
    n_ambiguous: int
    n_observed: int
    batch_size: int
    min_group_count: int
    high_missing_rate: float
    low_missing_rate: float
    ambiguous_low: float
    ambiguous_high: float


def deep_update(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_update(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path: str | None) -> Config:
    raw = DEFAULT_CONFIG
    if path:
        if yaml is None:
            raise RuntimeError("PyYAML is required when --config is used.")
        with open(path, "r", encoding="utf-8") as f:
            raw = deep_update(DEFAULT_CONFIG, yaml.safe_load(f) or {})

    paths = raw["paths"]
    sampling = raw["sampling"]
    thresholds = raw["thresholds"]
    return Config(
        resources_csv=Path(paths["resources_csv"]),
        topic_stats_csv=Path(paths["topic_stats_csv"]),
        skill_stats_csv=Path(paths["skill_stats_csv"]),
        output_dir=Path(paths["output_dir"]),
        report_dir=Path(paths["report_dir"]),
        random_seed=int(sampling["random_seed"]),
        total_candidates=int(sampling["total_candidates"]),
        n_structural=int(sampling["structural_absence_candidates"]),
        n_accidental=int(sampling["accidental_missing_candidates"]),
        n_ambiguous=int(sampling["ambiguous_missing_candidates"]),
        n_observed=int(sampling["observed_reference_candidates"]),
        batch_size=int(sampling.get("batch_size", 75)),
        min_group_count=int(thresholds["min_group_count"]),
        high_missing_rate=float(thresholds["high_missing_rate"]),
        low_missing_rate=float(thresholds["low_missing_rate"]),
        ambiguous_low=float(thresholds["ambiguous_low"]),
        ambiguous_high=float(thresholds["ambiguous_high"]),
    )


def parse_choices(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value)
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return " | ".join(str(item) for item in parsed)
    except json.JSONDecodeError:
        pass
    return text


def shorten(text: Any, max_chars: int = 700) -> str:
    if pd.isna(text):
        return ""
    value = " ".join(str(text).replace("\r", " ").replace("\n", " ").split())
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3] + "..."


def attach_group_stats(resources: pd.DataFrame, topic_stats: pd.DataFrame, skill_stats: pd.DataFrame) -> pd.DataFrame:
    topic_cols = topic_stats[["topic", "n", "missing_rate"]].rename(
        columns={"n": "topic_count", "missing_rate": "topic_missing_rate"}
    )
    skill_cols = skill_stats[["skill", "n", "missing_rate"]].rename(
        columns={"n": "skill_count", "missing_rate": "skill_missing_rate"}
    )
    data = resources.merge(topic_cols, on="topic", how="left").merge(skill_cols, on="skill", how="left")
    for col in ["topic_count", "skill_count"]:
        data[col] = data[col].fillna(0).astype(int)
    for col in ["topic_missing_rate", "skill_missing_rate"]:
        data[col] = data[col].fillna(data["has_image"].map({1: 0.0, 0: 1.0}))
    return data


def sample_frame(df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    if n <= 0 or df.empty:
        return df.head(0).copy()
    if len(df) <= n:
        return df.sample(frac=1.0, random_state=seed).copy()
    return df.sample(n=n, random_state=seed).copy()


def with_candidate_metadata(df: pd.DataFrame, candidate_type: str, reason: str) -> pd.DataFrame:
    out = df.copy()
    out["suggested_missing_type"] = candidate_type
    out["candidate_reason"] = reason
    return out


def build_candidates(data: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    missing = data[data["has_image"] == 0].copy()
    observed = data[data["has_image"] == 1].copy()

    missing_reliable_topic = missing["topic_count"] >= cfg.min_group_count
    missing_reliable_skill = missing["skill_count"] >= cfg.min_group_count
    missing_high_topic = missing_reliable_topic & (missing["topic_missing_rate"] >= cfg.high_missing_rate)
    missing_high_skill = missing_reliable_skill & (missing["skill_missing_rate"] >= cfg.high_missing_rate)
    missing_low_topic = missing_reliable_topic & (missing["topic_missing_rate"] <= cfg.low_missing_rate)
    missing_low_skill = missing_reliable_skill & (missing["skill_missing_rate"] <= cfg.low_missing_rate)
    missing_mid_topic = missing_reliable_topic & missing["topic_missing_rate"].between(
        cfg.ambiguous_low, cfg.ambiguous_high, inclusive="both"
    )
    missing_mid_skill = missing_reliable_skill & missing["skill_missing_rate"].between(
        cfg.ambiguous_low, cfg.ambiguous_high, inclusive="both"
    )

    structural_pool = missing[missing_high_topic | missing_high_skill].copy()
    accidental_pool = missing[(missing_low_topic | missing_low_skill) & ~(missing_high_topic | missing_high_skill)].copy()
    ambiguous_pool = missing[
        (missing_mid_topic | missing_mid_skill)
        & ~(missing_high_topic | missing_high_skill)
        & ~(missing_low_topic | missing_low_skill)
    ].copy()

    if len(ambiguous_pool) < cfg.n_ambiguous:
        selected_ids = set(structural_pool["resource_id"]).union(set(accidental_pool["resource_id"]))
        fallback = missing[~missing["resource_id"].isin(selected_ids)].copy()
        ambiguous_pool = pd.concat([ambiguous_pool, fallback], ignore_index=True).drop_duplicates("resource_id")

    observed_reliable_topic = observed["topic_count"] >= cfg.min_group_count
    observed_reliable_skill = observed["skill_count"] >= cfg.min_group_count
    observed_low_topic = observed_reliable_topic & (observed["topic_missing_rate"] <= cfg.low_missing_rate)
    observed_low_skill = observed_reliable_skill & (observed["skill_missing_rate"] <= cfg.low_missing_rate)
    observed_pool = observed[observed_low_topic | observed_low_skill].copy()
    if len(observed_pool) < cfg.n_observed:
        observed_pool = observed.copy()

    structural = with_candidate_metadata(
        sample_frame(structural_pool, cfg.n_structural, cfg.random_seed),
        "structural_absence_candidate",
        f"has_image=0 and topic/skill missing_rate >= {cfg.high_missing_rate}",
    )
    accidental = with_candidate_metadata(
        sample_frame(accidental_pool, cfg.n_accidental, cfg.random_seed + 1),
        "accidental_missing_candidate",
        f"has_image=0 but reliable topic/skill missing_rate <= {cfg.low_missing_rate}; check sparse skill stats manually",
    )
    selected = set(structural["resource_id"]).union(set(accidental["resource_id"]))
    ambiguous_pool = ambiguous_pool[~ambiguous_pool["resource_id"].isin(selected)]
    ambiguous = with_candidate_metadata(
        sample_frame(ambiguous_pool, cfg.n_ambiguous, cfg.random_seed + 2),
        "ambiguous_missing_candidate",
        f"has_image=0 and topic/skill missing_rate in [{cfg.ambiguous_low}, {cfg.ambiguous_high}] or fallback",
    )
    observed = with_candidate_metadata(
        sample_frame(observed_pool, cfg.n_observed, cfg.random_seed + 3),
        "observed_reference",
        "has_image=1 reference sample for calibration",
    )

    candidates = pd.concat([structural, accidental, ambiguous, observed], ignore_index=True, sort=False)
    candidates = candidates.drop_duplicates("resource_id")
    candidates = candidates.sample(frac=1.0, random_state=cfg.random_seed).reset_index(drop=True)
    candidates.insert(0, "annotation_id", [f"mt{i:04d}" for i in range(1, len(candidates) + 1)])
    candidates["human_label"] = ""
    candidates["label_confidence"] = ""
    candidates["label_note"] = ""

    candidates["choices"] = candidates["choices_json"].map(parse_choices)
    candidates["question"] = candidates["question"].map(shorten)
    candidates["lecture"] = candidates["lecture"].map(shorten)
    candidates["solution"] = candidates["solution"].map(shorten)
    return candidates


def select_output_columns(candidates: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "annotation_id",
        "resource_id",
        "original_id",
        "split",
        "has_image",
        "suggested_missing_type",
        "candidate_reason",
        "human_label",
        "label_confidence",
        "label_note",
        "subject",
        "topic",
        "topic_count",
        "topic_missing_rate",
        "skill",
        "skill_count",
        "skill_missing_rate",
        "grade",
        "category",
        "question",
        "choices",
        "answer",
        "hint",
        "lecture",
        "solution",
        "text_length",
        "word_count",
    ]
    return candidates[[col for col in columns if col in candidates.columns]]


def df_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_无记录。_"
    view = df.copy().fillna("NA").astype(str)
    headers = list(view.columns)
    rows = view.values.tolist()
    widths = [max(len(header), *(len(row[idx]) for row in rows)) for idx, header in enumerate(headers)]

    def fmt(values: list[str]) -> str:
        return "| " + " | ".join(value.ljust(widths[idx]) for idx, value in enumerate(values)) + " |"

    return "\n".join([fmt(headers), "| " + " | ".join("-" * width for width in widths) + " |", *(fmt(row) for row in rows)])


def write_summary(candidates: pd.DataFrame, pools: pd.DataFrame, cfg: Config) -> None:
    cfg.report_dir.mkdir(parents=True, exist_ok=True)
    type_counts = candidates["suggested_missing_type"].value_counts().rename_axis("candidate_type").reset_index(name="n")
    split_counts = candidates.groupby(["suggested_missing_type", "split"]).size().reset_index(name="n")
    topic_counts = (
        candidates.groupby(["suggested_missing_type", "topic"])
        .size()
        .reset_index(name="n")
        .sort_values(["suggested_missing_type", "n"], ascending=[True, False])
        .groupby("suggested_missing_type")
        .head(10)
    )
    lines = [
        "# Exp0.1 缺失类型标注候选集汇总",
        "",
        f"- 候选样本数：{len(candidates)}",
        f"- 来源资源表：{cfg.resources_csv}",
        f"- 最小分组样本数：{cfg.min_group_count}",
        f"- 高缺失率阈值：{cfg.high_missing_rate}",
        f"- 低缺失率阈值：{cfg.low_missing_rate}",
        "",
        "## 候选类型计数",
        "",
        df_to_markdown(type_counts),
        "",
        "## 数据划分计数",
        "",
        df_to_markdown(split_counts),
        "",
        "## 各候选类型的主要 Topic",
        "",
        df_to_markdown(topic_counts),
        "",
        "## 标注说明",
        "",
        "`suggested_missing_type` 仅作为抽样提示。请将 `human_label` 填为以下之一：",
        "",
        "- `observed`",
        "- `accidental_missing`",
        "- `structural_absence`",
        "- `ambiguous`",
        "",
        "不要仅根据 `has_image=0` 推断 `structural_absence`；需要判断图像对理解或解题是否具有教学必要性。",
        "",
    ]
    (cfg.report_dir / "annotation_candidate_summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_guidelines(cfg: Config) -> None:
    lines = [
        "# 缺失类型标注指南",
        "",
        "## 目标",
        "",
        "判断一个无图 ScienceQA 题目是缺少有教学价值的视觉模态，还是本身就是自然的纯文本题目。",
        "",
        "## 标签",
        "",
        "| 标签 | 定义 | 判断规则 |",
        "| --- | --- | --- |",
        "| `observed` | 原始题目有图像。 | 用于 `has_image=1` 的参考样本。 |",
        "| `structural_absence` | 题目不依赖图像即可理解和求解，教学上不需要图。 | 题目主要涉及语言、定义、抽象推理、事实回忆或纯文本证据。 |",
        "| `accidental_missing` | 题目通常需要或明显受益于视觉信息，但该记录中没有图。 | 题目涉及地图、图表、图形、物体属性、空间布局或视觉比较，但 `has_image=0`。 |",
        "| `ambiguous` | 是否需要图像无法明确判断。 | 当图像可能有帮助，但文本也包含足够信息，或题目表述不充分时使用。 |",
        "",
        "## 重要规则",
        "",
        "不要自动把 `suggested_missing_type` 复制到 `human_label`。它只是基于 topic/skill 缺失率统计得到的抽样提示。",
        "",
        "## 推荐标注流程",
        "",
        "1. 阅读 `question`、`choices`、`hint`、`lecture` 和 `solution`。",
        "2. 检查 `has_image`。",
        "3. 如果 `has_image=1`，除非该行明显异常，否则标为 `observed`。",
        "4. 如果 `has_image=0`，判断图像是否具有教学必要性。",
        "5. 在 `label_confidence` 中填写 `high`、`medium` 或 `low`。",
        "6. 在 `label_note` 中写简短证据，尤其是在不同意 `suggested_missing_type` 时。",
        "",
        "## 示例",
        "",
        "- 明喻/隐喻、标点、语法：通常是 `structural_absence`。",
        "- 地图阅读、地理位置、图像比较：如果 `has_image=0`，通常是 `accidental_missing`。",
        "- 生物分类或物理属性：需要看具体题目；文本可能足够，但图像也可能明显有帮助。",
        "",
    ]
    (cfg.report_dir / "ANNOTATION_GUIDELINES.md").write_text("\n".join(lines), encoding="utf-8")


def write_batches(output: pd.DataFrame, cfg: Config) -> None:
    batch_dir = cfg.output_dir / "batches"
    batch_dir.mkdir(parents=True, exist_ok=True)
    if cfg.batch_size <= 0:
        return
    for idx, start in enumerate(range(0, len(output), cfg.batch_size), start=1):
        batch = output.iloc[start : start + cfg.batch_size].copy()
        batch_path = batch_dir / f"missing_type_annotation_batch_{idx:02d}.csv"
        batch.to_csv(batch_path, index=False, encoding="utf-8-sig")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build missing-type annotation candidates.")
    parser.add_argument("--config", default="configs/exp0_1_missing_type_annotation.yaml")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--report-dir", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    if args.output_dir:
        cfg.output_dir = Path(args.output_dir)
    if args.report_dir:
        cfg.report_dir = Path(args.report_dir)

    resources = pd.read_csv(cfg.resources_csv)
    topic_stats = pd.read_csv(cfg.topic_stats_csv)
    skill_stats = pd.read_csv(cfg.skill_stats_csv)
    data = attach_group_stats(resources, topic_stats, skill_stats)
    candidates = build_candidates(data, cfg)
    output = select_output_columns(candidates)

    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = cfg.output_dir / "missing_type_annotation_candidates.csv"
    output.to_csv(output_path, index=False, encoding="utf-8-sig")
    write_summary(output, data, cfg)
    write_guidelines(cfg)
    write_batches(output, cfg)

    print(f"Candidates: {len(output)}")
    print(f"Output: {output_path}")
    print(f"Summary: {cfg.report_dir / 'annotation_candidate_summary.md'}")
    print(f"Guidelines: {cfg.report_dir / 'ANNOTATION_GUIDELINES.md'}")


if __name__ == "__main__":
    main()
