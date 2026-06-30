"""Exp1.0 教育多模态证据统一 schema 样例构建。

当前先处理本地已有的 ScienceQA，并为 TQA / AI2D 记录目标字段映射。
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


DEFAULT_CONFIG: dict[str, Any] = {
    "paths": {
        "report_dir": "reports/exp1_educational_mm_schema",
        "sample_dir": "data/educational_mm/schema_samples",
    },
    "datasets": {
        "scienceqa": {
            "resources_csv": "data/scienceqa/processed/resources.csv",
            "sample_size": 200,
            "random_seed": 42,
        },
        "tqa": {"raw_dir": "data/tqa/raw", "status": "pending_local_data"},
        "ai2d": {"raw_dir": "data/ai2d/raw", "status": "pending_local_data"},
    },
    "schema": {
        "columns": [
            "dataset",
            "sample_id",
            "original_id",
            "split",
            "question",
            "choices",
            "answer",
            "text_context",
            "image_ref",
            "has_image",
            "subject",
            "topic",
            "skill",
            "evidence_type",
            "modality_case",
            "answer_format",
            "source_task",
        ]
    },
}


@dataclass
class Config:
    report_dir: Path
    sample_dir: Path
    scienceqa_resources_csv: Path
    scienceqa_sample_size: int
    scienceqa_random_seed: int
    tqa_raw_dir: Path
    ai2d_raw_dir: Path
    schema_columns: list[str]


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
    scienceqa = raw["datasets"]["scienceqa"]
    return Config(
        report_dir=Path(raw["paths"]["report_dir"]),
        sample_dir=Path(raw["paths"]["sample_dir"]),
        scienceqa_resources_csv=Path(scienceqa["resources_csv"]),
        scienceqa_sample_size=int(scienceqa["sample_size"]),
        scienceqa_random_seed=int(scienceqa["random_seed"]),
        tqa_raw_dir=Path(raw["datasets"]["tqa"]["raw_dir"]),
        ai2d_raw_dir=Path(raw["datasets"]["ai2d"]["raw_dir"]),
        schema_columns=list(raw["schema"]["columns"]),
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


def join_context(row: pd.Series) -> str:
    parts = []
    for label, col in [("hint", "hint"), ("lecture", "lecture"), ("solution", "solution")]:
        value = row.get(col, "")
        if pd.notna(value) and str(value).strip():
            parts.append(f"{label}: {str(value).strip()}")
    return "\n".join(parts)


def evidence_type(has_image: int, text_context: str) -> str:
    has_text_evidence = bool(text_context.strip())
    if has_image and has_text_evidence:
        return "text_image"
    if has_image:
        return "image_only_context"
    if has_text_evidence:
        return "text_only"
    return "question_only"


def modality_case(has_image: int) -> str:
    return "question_with_image" if has_image else "question_without_image"


def build_scienceqa_schema(cfg: Config) -> pd.DataFrame:
    data = pd.read_csv(cfg.scienceqa_resources_csv)
    out = pd.DataFrame(index=data.index)
    out["dataset"] = "scienceqa"
    out["sample_id"] = data["resource_id"]
    out["original_id"] = data["original_id"]
    out["split"] = data["split"]
    out["question"] = data["question"].fillna("").astype(str)
    out["choices"] = data["choices_json"].map(parse_choices)
    out["answer"] = data["answer"].fillna("").astype(str)
    out["text_context"] = data.apply(join_context, axis=1)
    out["image_ref"] = data["image_ref"].fillna("").astype(str)
    out["has_image"] = pd.to_numeric(data["has_image"], errors="coerce").fillna(0).astype(int)
    out["subject"] = data["subject"].fillna("").astype(str)
    out["topic"] = data["topic"].fillna("").astype(str)
    out["skill"] = data["skill"].fillna("").astype(str)
    out["evidence_type"] = [evidence_type(int(row.has_image), row.text_context) for row in out.itertuples()]
    out["modality_case"] = out["has_image"].map(modality_case)
    out["answer_format"] = "multiple_choice"
    out["source_task"] = "educational_science_qa"
    return out[cfg.schema_columns]


def sample_schema(data: pd.DataFrame, sample_size: int, random_seed: int) -> pd.DataFrame:
    if len(data) <= sample_size:
        return data.copy()
    # Keep image/no-image cases visible in the schema sample.
    grouped = []
    per_group = max(1, sample_size // max(1, data["has_image"].nunique()))
    for _, frame in data.groupby("has_image"):
        grouped.append(frame.sample(n=min(per_group, len(frame)), random_state=random_seed))
    sample = pd.concat(grouped, ignore_index=True)
    if len(sample) < sample_size:
        rest = data[~data["sample_id"].isin(sample["sample_id"])]
        sample = pd.concat(
            [sample, rest.sample(n=min(sample_size - len(sample), len(rest)), random_state=random_seed)],
            ignore_index=True,
        )
    return sample.sample(frac=1.0, random_state=random_seed).head(sample_size)


def df_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_无记录。_"
    view = df.fillna("").astype(str)
    headers = list(view.columns)
    rows = view.values.tolist()
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        safe = [cell.replace("\n", "<br>").replace("|", "\\|") for cell in row]
        lines.append("| " + " | ".join(safe) + " |")
    return "\n".join(lines)


def coverage_rows(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in data.columns:
        non_empty = data[column].notna() & (data[column].astype(str).str.len() > 0)
        rows.append(
            {
                "column": column,
                "non_empty": int(non_empty.sum()),
                "coverage": round(float(non_empty.mean()), 4),
            }
        )
    return pd.DataFrame(rows)


def write_summary(cfg: Config, scienceqa: pd.DataFrame, sample_path: Path) -> None:
    cfg.report_dir.mkdir(parents=True, exist_ok=True)
    dataset_rows = pd.DataFrame(
        [
            {
                "dataset": "ScienceQA",
                "local_status": "已接入",
                "sample_count": len(scienceqa),
                "has_image_count": int(scienceqa["has_image"].sum()),
                "text_context_coverage": round(float((scienceqa["text_context"].str.len() > 0).mean()), 4),
                "next_action": "作为统一 schema 和 RC1/RC2 pilot 数据",
            },
            {
                "dataset": "TQA / CK12",
                "local_status": "待接入",
                "sample_count": "",
                "has_image_count": "",
                "text_context_coverage": "",
                "next_action": f"把原始文件放入 {cfg.tqa_raw_dir} 后编写 adapter",
            },
            {
                "dataset": "AI2D",
                "local_status": "待接入",
                "sample_count": "",
                "has_image_count": "",
                "text_context_coverage": "",
                "next_action": f"把原始文件放入 {cfg.ai2d_raw_dir} 后编写 adapter",
            },
        ]
    )
    mapping_rows = pd.DataFrame(
        [
            {"schema_column": "question", "ScienceQA": "question", "TQA": "question", "AI2D": "question"},
            {"schema_column": "choices", "ScienceQA": "choices_json", "TQA": "answer choices", "AI2D": "answer choices"},
            {"schema_column": "answer", "ScienceQA": "answer", "TQA": "answer", "AI2D": "correct answer"},
            {"schema_column": "text_context", "ScienceQA": "hint + lecture + solution", "TQA": "textbook paragraph", "AI2D": "diagram metadata / optional text"},
            {"schema_column": "image_ref", "ScienceQA": "image_ref", "TQA": "figure / diagram path", "AI2D": "diagram image path"},
            {"schema_column": "topic", "ScienceQA": "topic", "TQA": "chapter / lesson", "AI2D": "diagram topic if available"},
            {"schema_column": "skill", "ScienceQA": "skill", "TQA": "learning objective if available", "AI2D": "question category if available"},
        ]
    )
    lines = [
        "# Exp1.0 教育多模态证据统一 Schema",
        "",
        "## 目标",
        "",
        "将 ScienceQA、TQA/CK12 和 AI2D 映射到同一套教育图文证据 schema，为后续 RC1 证据对齐检索、RC2 模态必要性判断和 RC3 证据约束推理提供统一输入。",
        "",
        "## 数据集状态",
        "",
        df_to_markdown(dataset_rows),
        "",
        "## 统一字段",
        "",
        df_to_markdown(pd.DataFrame({"column": cfg.schema_columns})),
        "",
        "## 字段映射计划",
        "",
        df_to_markdown(mapping_rows),
        "",
        "## ScienceQA 字段覆盖率",
        "",
        df_to_markdown(coverage_rows(scienceqa)),
        "",
        "## 输出",
        "",
        f"- ScienceQA schema sample：`{sample_path}`",
        "",
        "## 下一步",
        "",
        "1. 接入 TQA / CK12，本地抽取 100-200 条样本映射到同一 schema。",
        "2. 接入 AI2D，本地抽取 100-200 条 diagram QA 样本映射到同一 schema。",
        "3. 基于统一 schema 实现 RC1 的 BM25 / Sentence-BERT / CLIP 检索基线。",
        "",
    ]
    (cfg.report_dir / "schema_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/exp1_educational_mm_schema.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)

    cfg.sample_dir.mkdir(parents=True, exist_ok=True)
    scienceqa = build_scienceqa_schema(cfg)
    sample = sample_schema(scienceqa, cfg.scienceqa_sample_size, cfg.scienceqa_random_seed)
    sample_path = cfg.sample_dir / "scienceqa_schema_sample.csv"
    sample.to_csv(sample_path, index=False, encoding="utf-8-sig")
    write_summary(cfg, scienceqa, sample_path)
    print(f"ScienceQA rows: {len(scienceqa)}")
    print(f"Sample: {sample_path}")
    print(f"Report: {cfg.report_dir / 'schema_summary.md'}")


if __name__ == "__main__":
    main()
