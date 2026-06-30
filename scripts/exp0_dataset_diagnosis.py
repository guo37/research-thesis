"""Exp0 ScienceQA dataset diagnosis.

This script builds the first unified ScienceQA schema and tests whether
image availability is structured by educational metadata.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.feature_selection import mutual_info_classif
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


DEFAULT_CONFIG = {
    "dataset": {
        "hf_name": "derek-thomas/ScienceQA",
        "hf_config": None,
        "cache_dir": "data/scienceqa/cache",
    },
    "paths": {
        "processed_dir": "data/scienceqa/processed",
        "report_dir": "reports/exp0_dataset_diagnosis",
    },
    "diagnosis": {
        "min_topic_count": 20,
        "min_skill_count": 20,
        "random_seed": 42,
        "test_size_when_no_split": 0.2,
        "validation_size_when_no_split": 0.1,
    },
    "models": {
        "max_categories": 500,
        "text_length_bins": 10,
    },
}


CONCEPT_COLUMNS = ["subject", "topic", "category", "skill", "grade"]
TEXT_COLUMNS = ["question", "hint", "task", "lecture", "solution"]
IMAGE_COLUMNS = ["image", "image_path", "image_file", "img", "picture", "figure"]
ID_COLUMNS = ["id", "qid", "question_id", "pid", "problem_id"]


@dataclass
class Config:
    hf_name: str
    hf_config: str | None
    cache_dir: Path
    processed_dir: Path
    report_dir: Path
    min_topic_count: int
    min_skill_count: int
    random_seed: int
    test_size_when_no_split: float
    validation_size_when_no_split: float
    max_categories: int
    text_length_bins: int


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
            user_config = yaml.safe_load(f) or {}
        raw = deep_update(DEFAULT_CONFIG, user_config)

    dataset = raw["dataset"]
    paths = raw["paths"]
    diagnosis = raw["diagnosis"]
    models = raw["models"]
    return Config(
        hf_name=dataset["hf_name"],
        hf_config=dataset.get("hf_config"),
        cache_dir=Path(dataset["cache_dir"]),
        processed_dir=Path(paths["processed_dir"]),
        report_dir=Path(paths["report_dir"]),
        min_topic_count=int(diagnosis["min_topic_count"]),
        min_skill_count=int(diagnosis["min_skill_count"]),
        random_seed=int(diagnosis["random_seed"]),
        test_size_when_no_split=float(diagnosis["test_size_when_no_split"]),
        validation_size_when_no_split=float(diagnosis["validation_size_when_no_split"]),
        max_categories=int(models["max_categories"]),
        text_length_bins=int(models["text_length_bins"]),
    )


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".jsonl", ".ndjson"}:
        return pd.read_json(path, lines=True)
    if suffix == ".json":
        return pd.read_json(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported input file: {path}")


def infer_split_from_filename(path: Path) -> str:
    stem = path.stem.lower()
    if "train" in stem:
        return "train"
    if "validation" in stem or stem == "val" or "val" in stem or "dev" in stem:
        return "validation"
    if "test" in stem:
        return "test"
    return "unknown"


def load_local_input(input_file: str | None, input_dir: str | None) -> pd.DataFrame:
    if input_file:
        df = read_table(Path(input_file))
        if "split" not in df.columns:
            df["split"] = "unknown"
        return df

    if not input_dir:
        raise ValueError("Either input_file or input_dir must be provided.")

    paths: list[Path] = []
    for ext in ("*.csv", "*.json", "*.jsonl", "*.ndjson", "*.parquet"):
        paths.extend(sorted(Path(input_dir).glob(ext)))
    if not paths:
        raise FileNotFoundError(f"No supported data files found under {input_dir}")

    frames = []
    for path in paths:
        df = read_table(path)
        if "split" not in df.columns:
            df["split"] = infer_split_from_filename(path)
        frames.append(df)
    return pd.concat(frames, ignore_index=True, sort=False)


def load_hf_dataset(cfg: Config) -> pd.DataFrame:
    from datasets import Dataset, DatasetDict, load_dataset

    kwargs: dict[str, Any] = {"cache_dir": str(cfg.cache_dir)}
    if cfg.hf_config:
        dataset = load_dataset(cfg.hf_name, cfg.hf_config, **kwargs)
    else:
        dataset = load_dataset(cfg.hf_name, **kwargs)

    frames = []
    if isinstance(dataset, DatasetDict):
        for split, split_ds in dataset.items():
            frame = split_ds.to_pandas()
            frame["split"] = split
            frames.append(frame)
    elif isinstance(dataset, Dataset):
        frame = dataset.to_pandas()
        if "split" not in frame.columns:
            frame["split"] = "unknown"
        frames.append(frame)
    else:
        raise TypeError(f"Unsupported dataset type: {type(dataset)!r}")

    return pd.concat(frames, ignore_index=True, sort=False)


def normalize_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"<bytes:{len(value)}>"
    if isinstance(value, (list, tuple)):
        return " | ".join(normalize_scalar(v) for v in value if normalize_scalar(v))
    if isinstance(value, dict):
        safe_value = {normalize_scalar(k): normalize_scalar(v) for k, v in value.items()}
        return json.dumps(safe_value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def normalize_choices(value: Any) -> str:
    if value is None:
        return "[]"
    if isinstance(value, float) and math.isnan(value):
        return "[]"
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return json.dumps(parsed, ensure_ascii=False)
        except json.JSONDecodeError:
            pass
        return json.dumps([value], ensure_ascii=False)
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if isinstance(value, (list, tuple)):
        return json.dumps([normalize_scalar(v) for v in value], ensure_ascii=False)
    return json.dumps([normalize_scalar(value)], ensure_ascii=False)


def image_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and math.isnan(value):
        return False
    if isinstance(value, (bytes, bytearray, memoryview)):
        return len(value) > 0
    if isinstance(value, str):
        stripped = value.strip().lower()
        return stripped not in {"", "none", "null", "nan", "[]", "{}"}
    if isinstance(value, np.ndarray):
        return value.size > 0
    if isinstance(value, (list, tuple, set)):
        return len(value) > 0
    if isinstance(value, dict):
        if not value:
            return False
        return any(image_present(v) for v in value.values())
    return True


def pick_first_column(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    lower_to_original = {c.lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in lower_to_original:
            return lower_to_original[candidate.lower()]
    return None


def normalize_split(value: Any) -> str:
    split = normalize_scalar(value).lower()
    if split in {"val", "dev"}:
        return "validation"
    if split in {"train", "training"}:
        return "train"
    if split in {"test", "testing"}:
        return "test"
    if split in {"validation", "valid"}:
        return "validation"
    return split or "unknown"


def ensure_splits(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    df = df.copy()
    df["split"] = df["split"].map(normalize_split)
    known = set(df["split"].unique())
    if {"train", "validation", "test"}.intersection(known):
        return df

    train_val, test = train_test_split(
        df,
        test_size=cfg.test_size_when_no_split,
        random_state=cfg.random_seed,
        stratify=df["has_image"] if df["has_image"].nunique() == 2 else None,
    )
    rel_val = cfg.validation_size_when_no_split / (1.0 - cfg.test_size_when_no_split)
    train, validation = train_test_split(
        train_val,
        test_size=rel_val,
        random_state=cfg.random_seed,
        stratify=train_val["has_image"] if train_val["has_image"].nunique() == 2 else None,
    )
    train = train.copy()
    validation = validation.copy()
    test = test.copy()
    train["split"] = "train"
    validation["split"] = "validation"
    test["split"] = "test"
    return pd.concat([train, validation, test], ignore_index=True, sort=False)


def build_resources(raw: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    df = raw.copy()
    image_col = pick_first_column(df, IMAGE_COLUMNS)
    id_col = pick_first_column(df, ID_COLUMNS)

    if "split" not in df.columns:
        df["split"] = "unknown"

    for col in TEXT_COLUMNS + CONCEPT_COLUMNS + ["answer"]:
        if col not in df.columns:
            df[col] = ""
    if "choices" not in df.columns:
        df["choices"] = None

    resources = pd.DataFrame()
    resources["resource_id"] = [f"r{i:06d}" for i in range(len(df))]
    resources["original_id"] = df[id_col].map(normalize_scalar) if id_col else resources["resource_id"]
    resources["split"] = df["split"].map(normalize_split)
    resources["question"] = df["question"].map(normalize_scalar)
    resources["choices_json"] = df["choices"].map(normalize_choices)
    resources["answer"] = df["answer"].map(normalize_scalar)
    resources["hint"] = df["hint"].map(normalize_scalar)
    resources["task"] = df["task"].map(normalize_scalar)
    resources["grade"] = df["grade"].map(normalize_scalar)
    resources["subject"] = df["subject"].map(normalize_scalar)
    resources["topic"] = df["topic"].map(normalize_scalar)
    resources["category"] = df["category"].map(normalize_scalar)
    resources["skill"] = df["skill"].map(normalize_scalar)
    resources["lecture"] = df["lecture"].map(normalize_scalar)
    resources["solution"] = df["solution"].map(normalize_scalar)

    if image_col:
        resources["has_image"] = df[image_col].map(image_present).astype(int)
        resources["image_ref"] = df[image_col].map(normalize_scalar)
    else:
        resources["has_image"] = 0
        resources["image_ref"] = ""

    full_text = (
        resources["question"]
        + " "
        + resources["choices_json"]
        + " "
        + resources["hint"]
        + " "
        + resources["lecture"]
        + " "
        + resources["solution"]
    ).str.strip()
    resources["text_length"] = full_text.str.len()
    resources["word_count"] = full_text.str.split().map(len)
    return ensure_splits(resources, cfg)


def make_concept_id(concept_type: str, name: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "_" for ch in name.strip())
    safe = "_".join(part for part in safe.split("_") if part)
    return f"{concept_type}:{safe[:80]}" if safe else f"{concept_type}:unknown"


def build_schema_tables(resources: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    concept_rows = []
    edge_rows = []
    for _, row in resources.iterrows():
        for concept_type in CONCEPT_COLUMNS:
            concept_name = normalize_scalar(row.get(concept_type, ""))
            if not concept_name:
                continue
            concept_id = make_concept_id(concept_type, concept_name)
            concept_rows.append(
                {
                    "concept_id": concept_id,
                    "concept_type": concept_type,
                    "concept_name": concept_name,
                }
            )
            edge_rows.append(
                {
                    "resource_id": row["resource_id"],
                    "concept_id": concept_id,
                    "relation": f"has_{concept_type}",
                    "source_field": concept_type,
                }
            )

    concepts = pd.DataFrame(concept_rows).drop_duplicates().sort_values(["concept_type", "concept_name"])
    resource_edges = pd.DataFrame(edge_rows).drop_duplicates()

    concept_edge_rows = []
    hierarchy = [("subject", "topic"), ("topic", "category"), ("category", "skill"), ("subject", "grade")]
    for _, row in resources.iterrows():
        for parent_type, child_type in hierarchy:
            parent_name = normalize_scalar(row.get(parent_type, ""))
            child_name = normalize_scalar(row.get(child_type, ""))
            if not parent_name or not child_name:
                continue
            concept_edge_rows.append(
                {
                    "source_concept_id": make_concept_id(parent_type, parent_name),
                    "target_concept_id": make_concept_id(child_type, child_name),
                    "relation": "parent_of",
                    "source": "scienceqa_metadata",
                }
            )
    concept_edges = pd.DataFrame(concept_edge_rows).drop_duplicates()

    modality_status = resources[
        [
            "resource_id",
            "split",
            "has_image",
            "image_ref",
            "subject",
            "topic",
            "skill",
            "grade",
            "text_length",
        ]
    ].copy()
    modality_status["image_status_initial"] = np.where(
        modality_status["has_image"] == 1,
        "observed",
        "missing_untyped",
    )
    modality_status["missing_type"] = ""
    modality_status["missing_type_note"] = "Exp0 only records has_image; structural_absence requires later annotation."
    return concepts, resource_edges, concept_edges, modality_status


def missingness_by_group(resources: pd.DataFrame, group_col: str) -> pd.DataFrame:
    grouped = (
        resources.groupby(group_col, dropna=False)
        .agg(
            n=("resource_id", "count"),
            has_image_count=("has_image", "sum"),
            has_image_rate=("has_image", "mean"),
        )
        .reset_index()
        .rename(columns={group_col: group_col})
    )
    grouped["missing_count"] = grouped["n"] - grouped["has_image_count"]
    grouped["missing_rate"] = 1.0 - grouped["has_image_rate"]
    return grouped.sort_values(["missing_rate", "n"], ascending=[False, False])


def chi_square_for_group(resources: pd.DataFrame, group_col: str) -> dict[str, float]:
    table = pd.crosstab(resources[group_col].fillna(""), resources["has_image"])
    if table.shape[0] < 2 or table.shape[1] < 2:
        return {"chi2": np.nan, "p_value": np.nan, "dof": np.nan}
    chi2, p_value, dof, _ = chi2_contingency(table)
    return {"chi2": float(chi2), "p_value": float(p_value), "dof": float(dof)}


def mutual_information(resources: pd.DataFrame, group_col: str) -> float:
    x = resources[[group_col]].fillna("").astype(str)
    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    encoded = encoder.fit_transform(x)
    mi = mutual_info_classif(encoded, resources["has_image"], discrete_features=True, random_state=0)
    return float(np.sum(mi))


def category_cap(series: pd.Series, max_categories: int) -> pd.Series:
    values = series.fillna("").astype(str)
    top = set(values.value_counts().head(max_categories).index)
    return values.where(values.isin(top), "__OTHER__")


def build_xy(resources: pd.DataFrame, features: list[str], cfg: Config) -> tuple[pd.DataFrame, pd.Series, list[str], list[str]]:
    x = resources[features].copy()
    categorical = []
    numeric = []
    for col in features:
        if col in {"text_length", "word_count"}:
            numeric.append(col)
        else:
            x[col] = category_cap(x[col], cfg.max_categories)
            categorical.append(col)
    y = resources["has_image"].astype(int)
    return x, y, categorical, numeric


def make_model(categorical: list[str], numeric: list[str], cfg: Config) -> Pipeline:
    try:
        one_hot = OneHotEncoder(handle_unknown="ignore", min_frequency=2)
    except TypeError:
        one_hot = OneHotEncoder(handle_unknown="ignore")

    transformers = []
    if categorical:
        transformers.append(("cat", one_hot, categorical))
    if numeric:
        transformers.append(
            (
                "num",
                Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]),
                numeric,
            )
        )
    preprocess = ColumnTransformer(transformers=transformers)
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", solver="lbfgs")
    return Pipeline([("preprocess", preprocess), ("clf", clf)])


def evaluate_predictions(y_true: pd.Series, y_score: np.ndarray, threshold: float = 0.5) -> dict[str, float]:
    y_pred = (y_score >= threshold).astype(int)
    out = {
        "auc": np.nan,
        "average_precision": np.nan,
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "positive_rate": float(np.mean(y_true)),
    }
    if len(np.unique(y_true)) == 2:
        out["auc"] = float(roc_auc_score(y_true, y_score))
        out["average_precision"] = float(average_precision_score(y_true, y_score))
    return out


def train_eval_by_split(resources: pd.DataFrame, feature_sets: dict[str, list[str]], cfg: Config) -> pd.DataFrame:
    train = resources[resources["split"] == "train"].copy()
    validation = resources[resources["split"] == "validation"].copy()
    test = resources[resources["split"] == "test"].copy()
    if train.empty:
        train = resources.copy()
    if validation.empty:
        validation = train.copy()
    if test.empty:
        test = validation.copy()

    rows = []
    for name, features in feature_sets.items():
        x_train, y_train, categorical, numeric = build_xy(train, features, cfg)
        for eval_split_name, eval_frame in [("validation", validation), ("test", test)]:
            x_eval, y_eval, _, _ = build_xy(eval_frame, features, cfg)
            if name == "majority":
                model = DummyClassifier(strategy="most_frequent")
                model.fit(x_train, y_train)
                if hasattr(model, "predict_proba"):
                    proba = model.predict_proba(x_eval)
                    if proba.shape[1] == 2:
                        score = proba[:, 1]
                    else:
                        score = np.full(len(x_eval), float(model.classes_[0] == 1))
                else:
                    score = model.predict(x_eval)
            else:
                if y_train.nunique() < 2:
                    score = np.full(len(x_eval), float(y_train.iloc[0]))
                else:
                    model = make_model(categorical, numeric, cfg)
                    model.fit(x_train, y_train)
                    score = model.predict_proba(x_eval)[:, 1]
            metrics = evaluate_predictions(y_eval, np.asarray(score))
            rows.append({"model": name, "eval_split": eval_split_name, **metrics, "features": ",".join(features)})
    return pd.DataFrame(rows)


def format_float(value: Any, digits: int = 4) -> str:
    try:
        if pd.isna(value):
            return "NA"
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def df_to_markdown(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "_No rows._"
    view = df.head(max_rows).copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: format_float(x))
    view = view.fillna("NA").astype(str)
    headers = list(view.columns)
    rows = view.values.tolist()
    widths = []
    for idx, header in enumerate(headers):
        widths.append(max(len(header), *(len(row[idx]) for row in rows)))

    def fmt_row(values: list[str]) -> str:
        return "| " + " | ".join(value.ljust(widths[idx]) for idx, value in enumerate(values)) + " |"

    separator = "| " + " | ".join("-" * width for width in widths) + " |"
    return "\n".join([fmt_row(headers), separator, *(fmt_row(row) for row in rows)])


def write_prediction_report(predictions: pd.DataFrame, path: Path) -> None:
    lines = [
        "# Missingness Prediction Results",
        "",
        "Target: `has_image`.",
        "",
        "Baselines are evaluated by split. The key comparison is whether `topic`, `skill`, and metadata improve over `majority` and `subject_only`.",
        "",
        df_to_markdown(predictions.sort_values(["eval_split", "model"])),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_dataset_report(
    resources: pd.DataFrame,
    by_subject: pd.DataFrame,
    by_topic: pd.DataFrame,
    by_skill: pd.DataFrame,
    mi_rows: list[dict[str, Any]],
    chi_rows: list[dict[str, Any]],
    predictions: pd.DataFrame,
    high_topics: pd.DataFrame,
    low_topics: pd.DataFrame,
    cfg: Config,
) -> None:
    split_counts = resources["split"].value_counts().rename_axis("split").reset_index(name="n")
    image_dist = resources["has_image"].value_counts().rename_axis("has_image").reset_index(name="n")
    image_dist["rate"] = image_dist["n"] / image_dist["n"].sum()
    concept_dist = pd.DataFrame(
        [
            {"field": field, "unique_values": resources[field].replace("", np.nan).nunique(), "non_empty": int((resources[field] != "").sum())}
            for field in ["subject", "topic", "skill", "grade", "category"]
        ]
    )
    mi_df = pd.DataFrame(mi_rows)
    chi_df = pd.DataFrame(chi_rows)

    best_test = predictions[predictions["eval_split"] == "test"].sort_values("auc", ascending=False)
    best_auc = best_test["auc"].dropna().max() if not best_test.empty else np.nan
    subject_auc = predictions[(predictions["eval_split"] == "test") & (predictions["model"] == "subject_only")]["auc"]
    full_auc = predictions[(predictions["eval_split"] == "test") & (predictions["model"] == "full_metadata_text")]["auc"]
    if not subject_auc.empty and not full_auc.empty and not pd.isna(subject_auc.iloc[0]) and not pd.isna(full_auc.iloc[0]):
        delta = full_auc.iloc[0] - subject_auc.iloc[0]
        conclusion = (
            "Preliminary support for structured missingness: full metadata improves over subject-only."
            if delta >= 0.03
            else "Weak or inconclusive structured-missingness signal: full metadata does not clearly improve over subject-only."
        )
    elif not pd.isna(best_auc):
        conclusion = (
            "Preliminary support for predictable missingness." if best_auc >= 0.65 else "Weak or inconclusive predictability signal."
        )
    else:
        conclusion = "Prediction conclusion unavailable because AUC could not be computed."

    lines = [
        "# Exp0 Dataset Statistics",
        "",
        "## 1. ScienceQA Basic Scale",
        "",
        f"- Total samples: {len(resources)}",
        f"- Overall has_image rate: {resources['has_image'].mean():.4f}",
        f"- Overall missing rate: {1.0 - resources['has_image'].mean():.4f}",
        "",
        "## 2. Train / Validation / Test Samples",
        "",
        df_to_markdown(split_counts),
        "",
        "## 3. Image Availability Distribution",
        "",
        df_to_markdown(image_dist),
        "",
        "## 4. Subject / Topic / Skill Distribution",
        "",
        df_to_markdown(concept_dist),
        "",
        "## 5. Subject-Level Image Missing Rate",
        "",
        df_to_markdown(by_subject),
        "",
        "## 6. Topic-Level Image Missing Rate",
        "",
        f"Main-topic threshold: `topic_count >= {cfg.min_topic_count}`.",
        "",
        df_to_markdown(by_topic[by_topic["n"] >= cfg.min_topic_count]),
        "",
        "## 7. Skill-Level Image Missing Rate",
        "",
        f"Main-skill threshold: `skill_count >= {cfg.min_skill_count}`.",
        "",
        df_to_markdown(by_skill[by_skill["n"] >= cfg.min_skill_count]),
        "",
        "## 8. Mutual Information",
        "",
        df_to_markdown(mi_df),
        "",
        "## 9. Chi-Square Tests",
        "",
        df_to_markdown(chi_df),
        "",
        "## 10. Missingness Prediction AUC",
        "",
        df_to_markdown(predictions),
        "",
        "## 11. High-MNAR / Low-MNAR Topic Candidates",
        "",
        "High-MNAR candidates are frequent topics with high missing rate. Low-MNAR candidates are frequent topics with low missing rate.",
        "",
        "### High-MNAR Topic Candidates",
        "",
        df_to_markdown(high_topics),
        "",
        "### Low-MNAR Topic Candidates",
        "",
        df_to_markdown(low_topics),
        "",
        "## 12. RC2 Continuation Decision",
        "",
        conclusion,
        "",
        "Caveat: Exp0 does not equate missing images with `structural_absence`. Missing-type labels require the later 300-500 sample annotation step.",
        "",
    ]
    (cfg.report_dir / "dataset_statistics.md").write_text("\n".join(lines), encoding="utf-8")


def save_outputs(resources: pd.DataFrame, cfg: Config) -> None:
    cfg.processed_dir.mkdir(parents=True, exist_ok=True)
    cfg.report_dir.mkdir(parents=True, exist_ok=True)

    resources.to_csv(cfg.processed_dir / "resources.csv", index=False, encoding="utf-8-sig")
    concepts, resource_edges, concept_edges, modality_status = build_schema_tables(resources)
    concepts.to_csv(cfg.processed_dir / "concepts.csv", index=False, encoding="utf-8-sig")
    resource_edges.to_csv(cfg.processed_dir / "resource_concept_edges.csv", index=False, encoding="utf-8-sig")
    concept_edges.to_csv(cfg.processed_dir / "concept_edges.csv", index=False, encoding="utf-8-sig")
    modality_status.to_csv(cfg.processed_dir / "modality_status_initial.csv", index=False, encoding="utf-8-sig")

    by_subject = missingness_by_group(resources, "subject")
    by_topic = missingness_by_group(resources, "topic")
    by_skill = missingness_by_group(resources, "skill")
    by_subject.to_csv(cfg.report_dir / "missingness_by_subject.csv", index=False, encoding="utf-8-sig")
    by_topic.to_csv(cfg.report_dir / "missingness_by_topic.csv", index=False, encoding="utf-8-sig")
    by_skill.to_csv(cfg.report_dir / "missingness_by_skill.csv", index=False, encoding="utf-8-sig")

    mi_rows = [{"field": field, "mutual_information": mutual_information(resources, field)} for field in ["subject", "topic", "skill", "grade"]]
    chi_rows = []
    for field in ["subject", "topic", "skill", "grade"]:
        chi_rows.append({"field": field, **chi_square_for_group(resources, field)})

    feature_sets = {
        "majority": ["subject"],
        "subject_only": ["subject"],
        "topic_only": ["topic"],
        "skill_only": ["skill"],
        "topic_skill": ["topic", "skill"],
        "subject_topic_skill": ["subject", "topic", "skill"],
        "full_metadata_text": ["subject", "topic", "skill", "grade", "text_length", "word_count"],
    }
    predictions = train_eval_by_split(resources, feature_sets, cfg)
    predictions.to_csv(cfg.report_dir / "prediction_results.csv", index=False, encoding="utf-8-sig")
    write_prediction_report(predictions, cfg.report_dir / "missingness_prediction_results.md")

    topic_main = by_topic[by_topic["n"] >= cfg.min_topic_count].copy()
    high_topics = topic_main.sort_values(["missing_rate", "n"], ascending=[False, False]).head(20)
    low_topics = topic_main.sort_values(["missing_rate", "n"], ascending=[True, False]).head(20)
    high_topics.to_csv(cfg.report_dir / "high_mnar_topics.csv", index=False, encoding="utf-8-sig")
    low_topics.to_csv(cfg.report_dir / "low_mnar_topics.csv", index=False, encoding="utf-8-sig")

    write_dataset_report(
        resources,
        by_subject,
        by_topic,
        by_skill,
        mi_rows,
        chi_rows,
        predictions,
        high_topics,
        low_topics,
        cfg,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Exp0 ScienceQA dataset diagnosis.")
    parser.add_argument("--config", default="configs/exp0_scienceqa.yaml", help="YAML config path.")
    parser.add_argument("--input-file", default=None, help="Local ScienceQA file: csv/json/jsonl/parquet.")
    parser.add_argument("--input-dir", default=None, help="Local ScienceQA directory with split files.")
    parser.add_argument("--hf-name", default=None, help="Override Hugging Face dataset name.")
    parser.add_argument("--hf-config", default=None, help="Override Hugging Face dataset config.")
    parser.add_argument("--processed-dir", default=None, help="Override processed output directory.")
    parser.add_argument("--report-dir", default=None, help="Override report output directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    if args.hf_name:
        cfg.hf_name = args.hf_name
    if args.hf_config:
        cfg.hf_config = args.hf_config
    if args.processed_dir:
        cfg.processed_dir = Path(args.processed_dir)
    if args.report_dir:
        cfg.report_dir = Path(args.report_dir)

    if args.input_file or args.input_dir:
        raw = load_local_input(args.input_file, args.input_dir)
    else:
        raw = load_hf_dataset(cfg)

    resources = build_resources(raw, cfg)
    save_outputs(resources, cfg)
    print(f"Processed samples: {len(resources)}")
    print(f"Processed tables: {cfg.processed_dir}")
    print(f"Reports: {cfg.report_dir}")


if __name__ == "__main__":
    main()
