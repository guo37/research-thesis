"""Exp1.0 教育多模态证据统一 schema 样例构建。

当前先处理本地已有的 ScienceQA，并为 TQA / AI2D 记录目标字段映射。
"""

from __future__ import annotations

import argparse
import ast
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
        "tqa": {
            "raw_dir": "data/tqa/raw",
            "hf_dataset": "notefill/ck12-tqa-instruction",
            "sample_size": 200,
            "max_scan": 8000,
            "random_seed": 42,
            "status": "hf_streaming",
        },
        "ai2d": {
            "raw_dir": "data/ai2d/raw",
            "hf_dataset": "lmms-lab/ai2d-no-mask",
            "split": "test",
            "sample_size": 200,
            "max_scan": 1000,
            "random_seed": 42,
            "status": "hf_streaming",
        },
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
    tqa_hf_dataset: str
    tqa_sample_size: int
    tqa_max_scan: int
    tqa_random_seed: int
    ai2d_raw_dir: Path
    ai2d_hf_dataset: str
    ai2d_split: str
    ai2d_sample_size: int
    ai2d_max_scan: int
    ai2d_random_seed: int
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
    tqa = raw["datasets"]["tqa"]
    ai2d = raw["datasets"]["ai2d"]
    return Config(
        report_dir=Path(raw["paths"]["report_dir"]),
        sample_dir=Path(raw["paths"]["sample_dir"]),
        scienceqa_resources_csv=Path(scienceqa["resources_csv"]),
        scienceqa_sample_size=int(scienceqa["sample_size"]),
        scienceqa_random_seed=int(scienceqa["random_seed"]),
        tqa_raw_dir=Path(tqa["raw_dir"]),
        tqa_hf_dataset=str(tqa.get("hf_dataset", "")),
        tqa_sample_size=int(tqa.get("sample_size", 200)),
        tqa_max_scan=int(tqa.get("max_scan", 8000)),
        tqa_random_seed=int(tqa.get("random_seed", 42)),
        ai2d_raw_dir=Path(ai2d["raw_dir"]),
        ai2d_hf_dataset=str(ai2d.get("hf_dataset", "")),
        ai2d_split=str(ai2d.get("split", "test")),
        ai2d_sample_size=int(ai2d.get("sample_size", 200)),
        ai2d_max_scan=int(ai2d.get("max_scan", 1000)),
        ai2d_random_seed=int(ai2d.get("random_seed", 42)),
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


def parse_list_like(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if pd.isna(value):
        return []
    text = str(value)
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except (SyntaxError, ValueError):
        pass
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        pass
    return [text] if text else []


def format_choices(options: list[str], labels: list[str] | None = None) -> str:
    if not options:
        return ""
    if labels and len(labels) == len(options):
        return " | ".join(f"{label}) {option}" for label, option in zip(labels, options))
    return " | ".join(str(option) for option in options)


def format_answer(answer: Any, options: list[str], labels: list[str] | None = None) -> str:
    text = "" if pd.isna(answer) else str(answer).strip()
    if not text:
        return ""
    if labels and text in labels:
        idx = labels.index(text)
        if idx < len(options):
            return f"{text}: {options[idx]}"
    if text.isdigit() and options:
        idx = int(text)
        if 0 <= idx < len(options):
            return f"{idx}: {options[idx]}"
    return text


def split_question_from_input(value: Any) -> str:
    text = "" if pd.isna(value) else str(value).strip()
    marker = "\n\nOptions:"
    if marker in text:
        return text.split(marker, 1)[0].strip()
    return text


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = "" if pd.isna(value) else str(value).strip().lower()
    return text in {"1", "true", "yes", "y"}


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


def load_hf_stream(dataset: str, split: str):
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("datasets is required for Hugging Face streaming sources.") from exc
    return load_dataset(dataset, split=split, streaming=True)


def build_tqa_row(item: dict[str, Any], split: str, index: int, cfg: Config) -> dict[str, Any]:
    options = parse_list_like(item.get("options", ""))
    labels = parse_list_like(item.get("option_labels", ""))
    has_image = as_bool(item.get("has_diagram", False))
    image_path = "" if str(item.get("image_path", "")).lower() == "none" else str(item.get("image_path", "")).strip()
    lesson = str(item.get("lesson_name", "")).strip()
    instruction = str(item.get("instruction", "")).strip()
    text_context = "\n".join(part for part in [f"lesson: {lesson}" if lesson else "", instruction] if part)
    return {
        "dataset": "tqa_ck12",
        "sample_id": str(item.get("id", f"tqa_{split}_{index:06d}")),
        "original_id": str(item.get("id", f"tqa_{split}_{index:06d}")),
        "split": split,
        "question": split_question_from_input(item.get("input", "")),
        "choices": format_choices(options, labels),
        "answer": format_answer(item.get("output", ""), options, labels),
        "text_context": text_context,
        "image_ref": f"hf://{cfg.tqa_hf_dataset}/{split}/{image_path}" if image_path else "",
        "has_image": int(has_image),
        "subject": "science",
        "topic": lesson,
        "skill": str(item.get("question_subtype", "") or item.get("question_type", "")).strip(),
        "evidence_type": evidence_type(int(has_image), text_context),
        "modality_case": modality_case(int(has_image)),
        "answer_format": "multiple_choice",
        "source_task": "ck12_textbook_qa",
    }


def build_tqa_schema_sample(cfg: Config) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    target_image = cfg.tqa_sample_size // 2
    target_no_image = cfg.tqa_sample_size - target_image
    image_count = 0
    no_image_count = 0
    scanned = 0
    for split in ["train", "validation", "test"]:
        stream = load_hf_stream(cfg.tqa_hf_dataset, split)
        for item in stream:
            scanned += 1
            row = build_tqa_row(item, split, scanned, cfg)
            if row["has_image"] and image_count < target_image:
                rows.append(row)
                image_count += 1
            elif not row["has_image"] and no_image_count < target_no_image:
                rows.append(row)
                no_image_count += 1
            if len(rows) >= cfg.tqa_sample_size or scanned >= cfg.tqa_max_scan:
                break
        if len(rows) >= cfg.tqa_sample_size or scanned >= cfg.tqa_max_scan:
            break
    return pd.DataFrame(rows, columns=cfg.schema_columns)


def build_ai2d_row(item: dict[str, Any], split: str, index: int, cfg: Config) -> dict[str, Any]:
    options = parse_list_like(item.get("options", ""))
    sample_id = f"ai2d_{split}_{index:06d}"
    return {
        "dataset": "ai2d",
        "sample_id": sample_id,
        "original_id": sample_id,
        "split": split,
        "question": str(item.get("question", "")).strip(),
        "choices": format_choices(options),
        "answer": format_answer(item.get("answer", ""), options),
        "text_context": "",
        "image_ref": f"hf://{cfg.ai2d_hf_dataset}/{split}/{index:06d}",
        "has_image": 1,
        "subject": "science",
        "topic": "diagram",
        "skill": "diagram_question_answering",
        "evidence_type": "image_only_context",
        "modality_case": "question_with_image",
        "answer_format": "multiple_choice",
        "source_task": "diagram_qa",
    }


def build_ai2d_schema_sample(cfg: Config) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    stream = load_hf_stream(cfg.ai2d_hf_dataset, cfg.ai2d_split)
    for index, item in enumerate(stream, start=1):
        rows.append(build_ai2d_row(item, cfg.ai2d_split, index, cfg))
        if len(rows) >= cfg.ai2d_sample_size or index >= cfg.ai2d_max_scan:
            break
    return pd.DataFrame(rows, columns=cfg.schema_columns)


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


def dataset_summary_row(name: str, data: pd.DataFrame, status: str, next_action: str) -> dict[str, Any]:
    if data.empty:
        return {
            "dataset": name,
            "local_status": status,
            "sample_count": 0,
            "has_image_count": 0,
            "text_context_coverage": 0.0,
            "next_action": next_action,
        }
    return {
        "dataset": name,
        "local_status": status,
        "sample_count": len(data),
        "has_image_count": int(data["has_image"].sum()),
        "text_context_coverage": round(float((data["text_context"].astype(str).str.len() > 0).mean()), 4),
        "next_action": next_action,
    }


def combined_coverage_rows(datasets: dict[str, pd.DataFrame], columns: list[str]) -> pd.DataFrame:
    rows = []
    for column in columns:
        row: dict[str, Any] = {"column": column}
        for name, data in datasets.items():
            if data.empty or column not in data.columns:
                row[name] = 0.0
                continue
            non_empty = data[column].notna() & (data[column].astype(str).str.len() > 0)
            row[name] = round(float(non_empty.mean()), 4)
        rows.append(row)
    return pd.DataFrame(rows)


def write_summary(
    cfg: Config,
    scienceqa: pd.DataFrame,
    tqa: pd.DataFrame,
    ai2d: pd.DataFrame,
    sample_paths: dict[str, Path],
) -> None:
    cfg.report_dir.mkdir(parents=True, exist_ok=True)
    dataset_rows = pd.DataFrame(
        [
            dataset_summary_row("ScienceQA", scienceqa, "已接入本地处理表", "作为统一 schema 和 RC1/RC2 pilot 数据"),
            dataset_summary_row("TQA / CK12", tqa, f"HF 流式样例：{cfg.tqa_hf_dataset}", "后续可下载官方完整包补齐原图路径"),
            dataset_summary_row("AI2D", ai2d, f"HF 流式样例：{cfg.ai2d_hf_dataset}", "作为 diagram QA 证据对齐和 wrong-image 实验数据"),
        ]
    )
    mapping_rows = pd.DataFrame(
        [
            {"schema_column": "question", "ScienceQA": "question", "TQA": "question", "AI2D": "question"},
            {"schema_column": "choices", "ScienceQA": "choices_json", "TQA": "answer choices", "AI2D": "answer choices"},
            {"schema_column": "answer", "ScienceQA": "answer", "TQA": "answer", "AI2D": "correct answer"},
            {"schema_column": "text_context", "ScienceQA": "hint + lecture + solution", "TQA": "lesson + instruction; official package can add textbook paragraph", "AI2D": "diagram metadata / optional text"},
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
        "## 字段覆盖率",
        "",
        df_to_markdown(combined_coverage_rows({"ScienceQA": scienceqa, "TQA_CK12": tqa, "AI2D": ai2d}, cfg.schema_columns)),
        "",
        "## 输出",
        "",
        f"- ScienceQA schema sample：`{sample_paths['scienceqa']}`",
        f"- TQA / CK12 schema sample：`{sample_paths['tqa']}`",
        f"- AI2D schema sample：`{sample_paths['ai2d']}`",
        "",
        "## 下一步",
        "",
        "1. 检查 TQA / CK12 样例中的 `has_image=1` 覆盖情况；如果不足，下载官方完整 TQA 包补齐 diagram 图像路径。",
        "2. 用 AI2D 构造 wrong-image hard negative，作为 RC1 和 RC2 的第一批鲁棒性实验。",
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
    scienceqa_sample = sample_schema(scienceqa, cfg.scienceqa_sample_size, cfg.scienceqa_random_seed)
    tqa_sample = build_tqa_schema_sample(cfg)
    ai2d_sample = build_ai2d_schema_sample(cfg)

    sample_paths = {
        "scienceqa": cfg.sample_dir / "scienceqa_schema_sample.csv",
        "tqa": cfg.sample_dir / "tqa_ck12_schema_sample.csv",
        "ai2d": cfg.sample_dir / "ai2d_schema_sample.csv",
    }
    scienceqa_sample.to_csv(sample_paths["scienceqa"], index=False, encoding="utf-8-sig")
    tqa_sample.to_csv(sample_paths["tqa"], index=False, encoding="utf-8-sig")
    ai2d_sample.to_csv(sample_paths["ai2d"], index=False, encoding="utf-8-sig")

    write_summary(cfg, scienceqa, tqa_sample, ai2d_sample, sample_paths)
    print(f"ScienceQA rows: {len(scienceqa)}")
    print(f"ScienceQA sample: {sample_paths['scienceqa']}")
    print(f"TQA sample: {sample_paths['tqa']} rows={len(tqa_sample)}")
    print(f"AI2D sample: {sample_paths['ai2d']} rows={len(ai2d_sample)}")
    print(f"Report: {cfg.report_dir / 'schema_summary.md'}")


if __name__ == "__main__":
    main()
