"""Exp1.3 AI2D 图像缓存。

从 Hugging Face `lmms-lab/ai2d-no-mask` 流式读取 diagram 图像，并按
统一 schema 样例中的 `image_ref` 生成本地图像缓存和 manifest。
"""

from __future__ import annotations

import argparse
import csv
import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
        "image_cache_dir": "data/ai2d/raw/images",
        "image_manifest": "reports/exp1_3_visual_evidence_retrieval/ai2d_image_manifest.csv",
    },
    "dataset": {
        "name": "ai2d",
        "hf_dataset": "lmms-lab/ai2d-no-mask",
        "split": "test",
        "max_scan": 1000,
    },
}


HF_REF_RE = re.compile(r"^hf://(?P<dataset>.+?)/(?P<split>[^/]+)/(?P<index>\d+)$")
IMAGE_KEYS = ["image", "diagram", "img", "picture"]


@dataclass
class Config:
    report_dir: Path
    schema_csv: Path
    image_cache_dir: Path
    image_manifest: Path
    dataset_name: str
    hf_dataset: str
    split: str
    max_scan: int


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
        print("PyYAML is not installed; using the built-in default Exp1.3 image cache config.")
    paths = raw["paths"]
    dataset = raw["dataset"]
    return Config(
        report_dir=Path(paths["report_dir"]),
        schema_csv=Path(paths["schema_csv"]),
        image_cache_dir=Path(paths["image_cache_dir"]),
        image_manifest=Path(paths["image_manifest"]),
        dataset_name=str(dataset["name"]),
        hf_dataset=str(dataset["hf_dataset"]),
        split=str(dataset["split"]),
        max_scan=int(dataset["max_scan"]),
    )


def parse_hf_index(image_ref: str) -> int | None:
    match = HF_REF_RE.match(str(image_ref).strip())
    if not match:
        return None
    return int(match.group("index"))


def load_targets(cfg: Config) -> pd.DataFrame:
    data = pd.read_csv(cfg.schema_csv)
    data = data[(data["dataset"] == cfg.dataset_name) & (data["image_ref"].fillna("").astype(str).str.len() > 0)].copy()
    data["hf_index"] = data["image_ref"].map(parse_hf_index)
    data = data[data["hf_index"].notna()].copy()
    data["hf_index"] = data["hf_index"].astype(int)
    return data.reset_index(drop=True)


def load_hf_stream(dataset: str, split: str):
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "datasets is required to cache AI2D images. Install requirements_exp1_visual.txt first."
        ) from exc
    return load_dataset(dataset, split=split, streaming=True)


def image_from_value(value: Any) -> Image.Image | None:
    if isinstance(value, Image.Image):
        return value.convert("RGB")
    if isinstance(value, bytes):
        return Image.open(io.BytesIO(value)).convert("RGB")
    if isinstance(value, dict):
        if value.get("bytes"):
            return Image.open(io.BytesIO(value["bytes"])).convert("RGB")
        path = value.get("path")
        if path and Path(path).exists():
            return Image.open(path).convert("RGB")
    if isinstance(value, str) and Path(value).exists():
        return Image.open(value).convert("RGB")
    return None


def extract_image(item: dict[str, Any]) -> Image.Image | None:
    for key in IMAGE_KEYS:
        if key in item:
            image = image_from_value(item[key])
            if image is not None:
                return image
    for value in item.values():
        image = image_from_value(value)
        if image is not None:
            return image
    return None


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


def write_summary(cfg: Config, manifest: pd.DataFrame) -> None:
    status_rows = (
        manifest.groupby("status")
        .agg(rows=("sample_id", "count"))
        .reset_index()
        .sort_values("status")
    )
    cached = manifest[manifest["status"] == "cached"]
    lines = [
        "# Exp1.3 AI2D 图像缓存",
        "",
        "## 目标",
        "",
        "为 AI2D schema 样例补齐本地图像缓存，给后续 CLIP / SigLIP 图文证据检索提供实际图像文件。",
        "",
        "## 缓存状态",
        "",
        df_to_markdown(status_rows),
        "",
        "## 输出",
        "",
        f"- manifest：`{cfg.image_manifest.as_posix()}`",
        f"- image cache：`{cfg.image_cache_dir.as_posix()}`",
        "",
    ]
    if not cached.empty:
        size_rows = cached[["sample_id", "local_image_path", "width", "height"]].head(10)
        lines.extend(["## 样例", "", df_to_markdown(size_rows), ""])
    lines.extend(
        [
            "## 下一步",
            "",
            "1. 使用 `scripts/exp1_3_visual_evidence_retrieval.py` 运行 CLIP / SigLIP 图文检索。",
            "2. 将 `wrong_image_candidates.csv` 作为 wrong-image confusion 评测候选池。",
            "",
        ]
    )
    (cfg.report_dir / "image_cache_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/exp1_3_visual_evidence_retrieval.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)

    cfg.report_dir.mkdir(parents=True, exist_ok=True)
    cfg.image_cache_dir.mkdir(parents=True, exist_ok=True)

    targets = load_targets(cfg)
    target_by_index = {int(row.hf_index): row for row in targets.itertuples()}
    manifest_rows: list[dict[str, Any]] = []
    seen: set[int] = set()

    stream = load_hf_stream(cfg.hf_dataset, cfg.split)
    max_needed = max(target_by_index) if target_by_index else 0
    scan_limit = min(max(cfg.max_scan, max_needed), cfg.max_scan)

    for index, item in enumerate(stream, start=1):
        if index > scan_limit:
            break
        if index not in target_by_index:
            continue
        row = target_by_index[index]
        seen.add(index)
        output_path = cfg.image_cache_dir / f"{row.sample_id}.png"
        try:
            image = extract_image(item)
            if image is None:
                raise ValueError("No image-like field found in HF item.")
            image.save(output_path)
            width, height = image.size
            status = "cached"
            error = ""
        except Exception as exc:  # pragma: no cover
            width = 0
            height = 0
            status = "error"
            error = str(exc)
        manifest_rows.append(
            {
                "dataset": cfg.dataset_name,
                "sample_id": row.sample_id,
                "image_ref": row.image_ref,
                "hf_index": index,
                "local_image_path": output_path.as_posix(),
                "status": status,
                "width": width,
                "height": height,
                "error": error,
            }
        )

    for index, row in target_by_index.items():
        if index in seen:
            continue
        manifest_rows.append(
            {
                "dataset": cfg.dataset_name,
                "sample_id": row.sample_id,
                "image_ref": row.image_ref,
                "hf_index": index,
                "local_image_path": "",
                "status": "not_found",
                "width": 0,
                "height": 0,
                "error": f"Index not reached within max_scan={cfg.max_scan}",
            }
        )

    manifest = pd.DataFrame(manifest_rows).sort_values(["hf_index", "sample_id"])
    manifest.to_csv(cfg.image_manifest, index=False, quoting=csv.QUOTE_MINIMAL)
    write_summary(cfg, manifest)
    cached_count = int((manifest["status"] == "cached").sum())
    print(f"Cached {cached_count}/{len(manifest)} AI2D images")
    print(f"Wrote {cfg.image_manifest}")


if __name__ == "__main__":
    main()
