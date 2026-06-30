"""Exp1.3 AI2D CLIP / SigLIP 图像证据检索 baseline。"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from PIL import Image

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


DEFAULT_CONFIG: dict[str, Any] = {
    "paths": {
        "report_dir": "reports/exp1_3_visual_evidence_retrieval",
        "schema_csv": "data/educational_mm/schema_samples/ai2d_schema_sample.csv",
        "image_manifest": "reports/exp1_3_visual_evidence_retrieval/ai2d_image_manifest.csv",
        "wrong_image_candidates": "reports/exp1_2_hard_negative_retrieval/wrong_image_candidates.csv",
    },
    "dataset": {"name": "ai2d"},
    "retrieval": {
        "query_columns": ["question", "choices", "topic", "skill"],
        "top_k": [1, 5, 10],
        "batch_size": 16,
    },
    "models": [
        {"name": "openai/clip-vit-base-patch32", "alias": "clip_vit_b32", "enabled": True},
        {"name": "google/siglip-base-patch16-224", "alias": "siglip_b16_224", "enabled": False},
    ],
}


@dataclass
class ModelConfig:
    name: str
    alias: str
    enabled: bool


@dataclass
class Config:
    report_dir: Path
    schema_csv: Path
    image_manifest: Path
    wrong_image_candidates: Path
    dataset_name: str
    query_columns: list[str]
    top_k: list[int]
    batch_size: int
    models: list[ModelConfig]


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
    if path and yaml is not None:
        with open(path, "r", encoding="utf-8") as f:
            raw = deep_update(DEFAULT_CONFIG, yaml.safe_load(f) or {})
    elif path and yaml is None:
        print("PyYAML is not installed; using the built-in default Exp1.3 visual retrieval config.")
    paths = raw["paths"]
    retrieval = raw["retrieval"]
    return Config(
        report_dir=Path(paths["report_dir"]),
        schema_csv=Path(paths["schema_csv"]),
        image_manifest=Path(paths["image_manifest"]),
        wrong_image_candidates=Path(paths["wrong_image_candidates"]),
        dataset_name=str(raw["dataset"]["name"]),
        query_columns=list(retrieval["query_columns"]),
        top_k=sorted(int(k) for k in retrieval["top_k"]),
        batch_size=int(retrieval["batch_size"]),
        models=[
            ModelConfig(name=str(item["name"]), alias=str(item["alias"]), enabled=bool(item.get("enabled", True)))
            for item in raw["models"]
        ],
    )


def normalize_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split())


def make_query(row: pd.Series, columns: list[str]) -> str:
    return " ".join(part for part in (normalize_text(row.get(col, "")) for col in columns) if part)


def load_eval_rows(cfg: Config) -> pd.DataFrame:
    schema = pd.read_csv(cfg.schema_csv)
    manifest = pd.read_csv(cfg.image_manifest)
    cached = manifest[manifest["status"] == "cached"].copy()
    data = schema.merge(
        cached[["image_ref", "local_image_path", "width", "height"]],
        on="image_ref",
        how="inner",
    )
    data = data[data["dataset"] == cfg.dataset_name].copy()
    data["query_text"] = data.apply(lambda row: make_query(row, cfg.query_columns), axis=1)
    data = data[data["query_text"].str.len() > 0].reset_index(drop=True)
    return data


def require_model_deps():
    try:
        import torch
        from transformers import AutoModel, AutoProcessor
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "torch and transformers are required for Exp1.3 visual retrieval. "
            "Install requirements_exp1_visual.txt first."
        ) from exc
    return torch, AutoModel, AutoProcessor


def batched(items: list[Any], batch_size: int):
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def normalize_embeddings(values):
    norm = values.norm(dim=-1, keepdim=True).clamp_min(1e-12)
    return values / norm


def feature_tensor(output):
    if hasattr(output, "norm"):
        return output
    for attr in ["text_embeds", "image_embeds", "pooler_output"]:
        value = getattr(output, attr, None)
        if value is not None:
            return value
    if isinstance(output, (tuple, list)) and output:
        return output[0]
    raise TypeError(f"Unsupported model feature output: {type(output)!r}")


def encode_with_model(model_cfg: ModelConfig, eval_rows: pd.DataFrame, cfg: Config) -> tuple[np.ndarray, np.ndarray]:
    torch, AutoModel, AutoProcessor = require_model_deps()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    processor = AutoProcessor.from_pretrained(model_cfg.name)
    model = AutoModel.from_pretrained(model_cfg.name).to(device)
    model.eval()

    text_features = []
    texts = eval_rows["query_text"].tolist()
    with torch.no_grad():
        for batch in batched(texts, cfg.batch_size):
            inputs = processor(text=batch, padding=True, truncation=True, return_tensors="pt").to(device)
            if hasattr(model, "get_text_features"):
                features = feature_tensor(model.get_text_features(**inputs))
            else:  # pragma: no cover
                output = model(**inputs)
                features = feature_tensor(output)
            text_features.append(normalize_embeddings(features).cpu())

    image_features = []
    paths = eval_rows["local_image_path"].tolist()
    with torch.no_grad():
        for batch in batched(paths, cfg.batch_size):
            images = [Image.open(path).convert("RGB") for path in batch]
            inputs = processor(images=images, return_tensors="pt").to(device)
            if hasattr(model, "get_image_features"):
                features = feature_tensor(model.get_image_features(**inputs))
            else:  # pragma: no cover
                output = model(**inputs)
                features = feature_tensor(output)
            image_features.append(normalize_embeddings(features).cpu())

    text_matrix = torch.cat(text_features, dim=0).numpy()
    image_matrix = torch.cat(image_features, dim=0).numpy()
    return text_matrix, image_matrix


def rank_from_scores(scores: np.ndarray) -> np.ndarray:
    return np.lexsort((np.arange(len(scores)), -scores))


def evaluate_full_retrieval(
    model_alias: str,
    eval_rows: pd.DataFrame,
    score_matrix: np.ndarray,
    cfg: Config,
) -> tuple[dict[str, Any], pd.DataFrame]:
    hits = {k: 0 for k in cfg.top_k}
    rr_sum = 0.0
    rows: list[dict[str, Any]] = []
    max_k = max(cfg.top_k)
    for idx, row in eval_rows.iterrows():
        ranking = rank_from_scores(score_matrix[idx])
        rank = int(np.where(ranking == idx)[0][0]) + 1
        rr_sum += 1.0 / rank
        for k in cfg.top_k:
            if rank <= k:
                hits[k] += 1
        top_indices = ranking[:max_k]
        rows.append(
            {
                "model": model_alias,
                "sample_id": row["sample_id"],
                "image_ref": row["image_ref"],
                "rank": rank,
                "positive_score": float(score_matrix[idx, idx]),
                "top_image_refs": json.dumps(eval_rows.iloc[top_indices]["image_ref"].tolist(), ensure_ascii=False),
            }
        )
    n = len(eval_rows)
    metrics: dict[str, Any] = {
        "model": model_alias,
        "dataset": cfg.dataset_name,
        "n_queries": n,
        "n_images": n,
        "mrr": rr_sum / n if n else 0.0,
    }
    for k in cfg.top_k:
        metrics[f"recall_at_{k}"] = hits[k] / n if n else 0.0
    return metrics, pd.DataFrame(rows)


def evaluate_wrong_images(
    model_alias: str,
    eval_rows: pd.DataFrame,
    score_matrix: np.ndarray,
    cfg: Config,
) -> pd.DataFrame:
    if not cfg.wrong_image_candidates.exists():
        return pd.DataFrame()
    candidates = pd.read_csv(cfg.wrong_image_candidates)
    ref_to_idx = {ref: idx for idx, ref in enumerate(eval_rows["image_ref"].tolist())}
    rows: list[dict[str, Any]] = []
    for _, row in candidates.iterrows():
        pos_idx = ref_to_idx.get(row["positive_image_ref"])
        neg_idx = ref_to_idx.get(row["negative_image_ref"])
        if pos_idx is None or neg_idx is None:
            continue
        positive_score = float(score_matrix[pos_idx, pos_idx])
        negative_score = float(score_matrix[pos_idx, neg_idx])
        rows.append(
            {
                "model": model_alias,
                "strategy": row["strategy"],
                "sample_id": row["sample_id"],
                "negative_sample_id": row["negative_sample_id"],
                "positive_score": positive_score,
                "negative_score": negative_score,
                "positive_margin": positive_score - negative_score,
                "wrong_image_confused": negative_score >= positive_score,
            }
        )
    return pd.DataFrame(rows)


def summarize_wrong_image(wrong_rows: pd.DataFrame) -> pd.DataFrame:
    if wrong_rows.empty:
        return pd.DataFrame()
    return (
        wrong_rows.groupby(["model", "strategy"])
        .agg(
            pairs=("sample_id", "count"),
            queries=("sample_id", "nunique"),
            wrong_image_confusion_rate=("wrong_image_confused", "mean"),
            mean_positive_margin=("positive_margin", "mean"),
        )
        .reset_index()
    )


def df_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_无记录。_"
    view = df.fillna("").astype(str)
    headers = list(view.columns)
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for _, row in view.iterrows():
        safe = [str(row[col]).replace("\n", "<br>").replace("|", "\\|") for col in headers]
        lines.append("| " + " | ".join(safe) + " |")
    return "\n".join(lines)


def format_float(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_summary(cfg: Config, metrics: pd.DataFrame, wrong_summary: pd.DataFrame, notes: list[str]) -> None:
    metric_view = metrics.copy()
    wrong_view = wrong_summary.copy()
    for frame in [metric_view, wrong_view]:
        for col in frame.columns:
            if frame[col].dtype.kind == "f":
                frame[col] = frame[col].map(format_float)
    lines = [
        "# Exp1.3 AI2D 图像证据检索 Baseline",
        "",
        "## 目标",
        "",
        "在已缓存的 AI2D diagram 图像上运行 CLIP / SigLIP 图文检索，评估题目文本是否能检索到对应图像证据，并用 Exp1.2 的 wrong-image 候选池计算干扰图混淆率。",
        "",
        "## 图像检索指标",
        "",
        df_to_markdown(metric_view),
        "",
        "## Wrong-image 指标",
        "",
        df_to_markdown(wrong_view),
        "",
    ]
    if notes:
        lines.extend(["## 运行备注", "", *[f"- {note}" for note in notes], ""])
    lines.extend(
        [
            "## 下一步",
            "",
            "1. 抽查 CLIP / SigLIP 的 wrong-image 混淆样例，区分题干相似、图示相似和标签重复三类错误。",
            "2. 将图像检索结果接入 RC2 wrong-image / drop-image 鲁棒推理实验。",
            "3. 后续如需提升 RC1，可加入教育 hard negative 训练或 reranker。",
            "",
        ]
    )
    (cfg.report_dir / "run_summary.md").write_text("\n".join(lines), encoding="utf-8")


def check_inputs(cfg: Config) -> None:
    cfg.report_dir.mkdir(parents=True, exist_ok=True)
    notes = []
    if not cfg.image_manifest.exists():
        notes.append(f"missing image manifest: {cfg.image_manifest}")
    else:
        manifest = pd.read_csv(cfg.image_manifest)
        cached = int((manifest["status"] == "cached").sum()) if "status" in manifest else 0
        notes.append(f"cached images: {cached}/{len(manifest)}")
    if not cfg.wrong_image_candidates.exists():
        notes.append(f"missing wrong-image candidates: {cfg.wrong_image_candidates}")
    else:
        candidates = pd.read_csv(cfg.wrong_image_candidates)
        notes.append(f"wrong-image candidate pairs: {len(candidates)}")
    write_summary(cfg, pd.DataFrame(), pd.DataFrame(), notes)
    print("; ".join(notes))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/exp1_3_visual_evidence_retrieval.yaml")
    parser.add_argument("--check-inputs", action="store_true")
    args = parser.parse_args()
    cfg = load_config(args.config)
    cfg.report_dir.mkdir(parents=True, exist_ok=True)

    if args.check_inputs:
        check_inputs(cfg)
        return

    eval_rows = load_eval_rows(cfg)
    if eval_rows.empty:
        raise RuntimeError("No cached AI2D images found. Run scripts/exp1_3_cache_ai2d_images.py first.")

    metric_rows: list[dict[str, Any]] = []
    ranking_frames: list[pd.DataFrame] = []
    wrong_frames: list[pd.DataFrame] = []
    notes: list[str] = []

    for model_cfg in cfg.models:
        if not model_cfg.enabled:
            notes.append(f"model disabled in config: {model_cfg.alias}")
            continue
        text_matrix, image_matrix = encode_with_model(model_cfg, eval_rows, cfg)
        score_matrix = text_matrix @ image_matrix.T
        metrics, rankings = evaluate_full_retrieval(model_cfg.alias, eval_rows, score_matrix, cfg)
        wrong_rows = evaluate_wrong_images(model_cfg.alias, eval_rows, score_matrix, cfg)
        metric_rows.append(metrics)
        ranking_frames.append(rankings)
        wrong_frames.append(wrong_rows)

    metrics = pd.DataFrame(metric_rows)
    rankings = pd.concat(ranking_frames, ignore_index=True, sort=False) if ranking_frames else pd.DataFrame()
    wrong_rows = pd.concat(wrong_frames, ignore_index=True, sort=False) if wrong_frames else pd.DataFrame()
    wrong_summary = summarize_wrong_image(wrong_rows)

    metrics.to_csv(cfg.report_dir / "metrics.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    rankings.to_csv(cfg.report_dir / "image_rankings.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    wrong_rows.to_csv(cfg.report_dir / "wrong_image_eval.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    wrong_summary.to_csv(cfg.report_dir / "wrong_image_metrics.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    write_summary(cfg, metrics, wrong_summary, notes)
    print(f"Wrote {cfg.report_dir}")


if __name__ == "__main__":
    main()
