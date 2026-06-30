"""Exp0.2 选择性补全门控基线。

预测缺图样本是结构性无图，还是需要图但数据中缺图。
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


DEFAULT_CONFIG: dict[str, Any] = {
    "paths": {
        "input_csv": "data/scienceqa/annotation/missing_type_annotation_candidates.csv",
        "resources_csv": "data/scienceqa/processed/resources.csv",
        "report_dir": "reports/exp0_2_selective_completion_gate",
        "full_prediction_csv": "reports/exp0_2_selective_completion_gate/full_missing_predictions.csv",
    },
    "target": {
        "negative_label": "structural_absence",
        "positive_labels": ["accidental_missing"],
    },
    "features": {
        "categorical": ["subject", "topic", "skill", "grade", "category"],
        "numeric": ["text_length", "word_count"],
        "text": ["question", "choices", "hint", "lecture", "solution"],
    },
    "model": {
        "random_seed": 42,
        "max_text_features": 3000,
        "threshold_grid": {"start": 0.05, "stop": 0.95, "step": 0.05},
    },
    "evaluation": {
        "group_holdout_fields": ["topic", "skill"],
        "validation_fraction": 0.20,
        "test_fraction": 0.20,
        "group_split_trials": 3000,
    },
    "prediction": {
        "model": "best_group_test",
    },
}


@dataclass
class Config:
    input_csv: Path
    resources_csv: Path
    report_dir: Path
    full_prediction_csv: Path
    negative_label: str
    positive_labels: list[str]
    categorical: list[str]
    numeric: list[str]
    text: list[str]
    random_seed: int
    max_text_features: int
    thresholds: list[float]
    group_holdout_fields: list[str]
    validation_fraction: float
    test_fraction: float
    group_split_trials: int
    prediction_model: str


@dataclass
class SplitScenario:
    name: str
    data: pd.DataFrame
    diagnostics: list[dict[str, Any]]


@dataclass
class ModelSpec:
    name: str
    model: Any
    feature_view: str
    tune_threshold: bool


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

    grid = raw["model"]["threshold_grid"]
    thresholds = np.arange(float(grid["start"]), float(grid["stop"]) + 1e-9, float(grid["step"]))
    paths = raw["paths"]
    evaluation = raw.get("evaluation", {})
    prediction = raw.get("prediction", {})
    return Config(
        input_csv=Path(paths["input_csv"]),
        resources_csv=Path(paths["resources_csv"]),
        report_dir=Path(paths["report_dir"]),
        full_prediction_csv=Path(paths["full_prediction_csv"]),
        negative_label=str(raw["target"]["negative_label"]),
        positive_labels=list(raw["target"]["positive_labels"]),
        categorical=list(raw["features"]["categorical"]),
        numeric=list(raw["features"]["numeric"]),
        text=list(raw["features"]["text"]),
        random_seed=int(raw["model"]["random_seed"]),
        max_text_features=int(raw["model"]["max_text_features"]),
        thresholds=[round(float(x), 4) for x in thresholds],
        group_holdout_fields=list(evaluation.get("group_holdout_fields", [])),
        validation_fraction=float(evaluation.get("validation_fraction", 0.20)),
        test_fraction=float(evaluation.get("test_fraction", 0.20)),
        group_split_trials=int(evaluation.get("group_split_trials", 3000)),
        prediction_model=str(prediction.get("model", "best_group_test")),
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


def add_model_features(data: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    out = data.copy()
    if "choices" not in out.columns and "choices_json" in out.columns:
        out["choices"] = out["choices_json"].map(parse_choices)
    for col in cfg.text:
        if col not in out.columns:
            out[col] = ""
    out["text_bundle"] = out[cfg.text].fillna("").astype(str).agg(" ".join, axis=1)
    for col in cfg.categorical:
        if col not in out.columns:
            out[col] = "<missing>"
        out[col] = out[col].fillna("<missing>").astype(str)
    for col in cfg.numeric:
        if col not in out.columns:
            out[col] = np.nan
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def prepare_labeled_data(cfg: Config) -> pd.DataFrame:
    data = pd.read_csv(cfg.input_csv)
    data = data[data["has_image"].astype(str) == "0"].copy()
    keep_labels = {cfg.negative_label, *cfg.positive_labels}
    data = data[data["human_label"].isin(keep_labels)].copy()
    data["target"] = data["human_label"].isin(cfg.positive_labels).astype(int)
    return add_model_features(data, cfg)


def prepare_full_missing_resources(cfg: Config) -> pd.DataFrame:
    data = pd.read_csv(cfg.resources_csv)
    data = data[data["has_image"].astype(str) == "0"].copy()
    return add_model_features(data, cfg)


def build_metadata_model(cfg: Config) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cfg.categorical),
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), cfg.numeric),
        ]
    )
    return Pipeline(
        steps=[
            ("features", preprocessor),
            (
                "classifier",
                LogisticRegression(class_weight="balanced", max_iter=2000, random_state=cfg.random_seed),
            ),
        ]
    )


def build_text_model(cfg: Config) -> Pipeline:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    max_features=cfg.max_text_features,
                    min_df=1,
                    strip_accents="unicode",
                ),
            ),
            (
                "classifier",
                LogisticRegression(class_weight="balanced", max_iter=2000, random_state=cfg.random_seed),
            ),
        ]
    )


def build_metadata_text_model(cfg: Config) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "text",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    max_features=cfg.max_text_features,
                    min_df=1,
                    strip_accents="unicode",
                ),
                "text_bundle",
            ),
            ("cat", OneHotEncoder(handle_unknown="ignore"), cfg.categorical),
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), cfg.numeric),
        ]
    )
    return Pipeline(
        steps=[
            ("features", preprocessor),
            (
                "classifier",
                LogisticRegression(class_weight="balanced", max_iter=2000, random_state=cfg.random_seed),
            ),
        ]
    )


def build_model_specs(cfg: Config) -> list[ModelSpec]:
    return [
        ModelSpec("majority", DummyClassifier(strategy="most_frequent"), "categorical", False),
        ModelSpec("metadata", build_metadata_model(cfg), "metadata", True),
        ModelSpec("text", build_text_model(cfg), "text", True),
        ModelSpec("metadata_text", build_metadata_text_model(cfg), "frame", True),
    ]


def select_features(data: pd.DataFrame, cfg: Config, feature_view: str) -> Any:
    if feature_view == "categorical":
        return data[cfg.categorical]
    if feature_view == "metadata":
        return data[cfg.categorical + cfg.numeric]
    if feature_view == "text":
        return data["text_bundle"]
    if feature_view == "frame":
        return data
    raise ValueError(f"Unknown feature view: {feature_view}")


def metrics_from_predictions(y_true: np.ndarray, y_pred: np.ndarray, score: np.ndarray | None = None) -> dict[str, Any]:
    labels = set(int(x) for x in y_true)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    out: dict[str, Any] = {
        "n": int(len(y_true)),
        "positive_rate": float(np.mean(y_true)) if len(y_true) else 0.0,
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred) if len(labels) == 2 else np.nan,
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "positive_f1": f1_score(y_true, y_pred, pos_label=1, zero_division=0),
        "positive_precision": precision_score(y_true, y_pred, pos_label=1, zero_division=0),
        "positive_recall": recall_score(y_true, y_pred, pos_label=1, zero_division=0),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }
    if score is not None and len(labels) == 2:
        out["pr_auc"] = average_precision_score(y_true, score)
    else:
        out["pr_auc"] = np.nan
    return out


def positive_scores(model: Any, x: Any) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        return model.predict_proba(x)[:, 1]
    if hasattr(model, "decision_function"):
        raw = model.decision_function(x)
        return 1 / (1 + np.exp(-raw))
    return model.predict(x)


def select_threshold(y_true: np.ndarray, scores: np.ndarray, thresholds: list[float]) -> tuple[float, dict[str, Any]]:
    best_threshold = 0.5
    best_metrics: dict[str, Any] | None = None
    for threshold in thresholds:
        pred = (scores >= threshold).astype(int)
        current = metrics_from_predictions(y_true, pred, scores)
        if best_metrics is None:
            best_threshold = threshold
            best_metrics = current
            continue
        key = (
            current["positive_f1"],
            current["balanced_accuracy"] if not np.isnan(current["balanced_accuracy"]) else -1.0,
            current["macro_f1"],
        )
        best_key = (
            best_metrics["positive_f1"],
            best_metrics["balanced_accuracy"] if not np.isnan(best_metrics["balanced_accuracy"]) else -1.0,
            best_metrics["macro_f1"],
        )
        if key > best_key:
            best_threshold = threshold
            best_metrics = current
    assert best_metrics is not None
    return best_threshold, best_metrics


def evaluate_model(
    scenario: str,
    spec: ModelSpec,
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    cfg: Config,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    model = spec.model
    train_x = select_features(train, cfg, spec.feature_view)
    val_x = select_features(val, cfg, spec.feature_view)
    test_x = select_features(test, cfg, spec.feature_view)
    train_y = train["target"].to_numpy()
    val_y = val["target"].to_numpy()
    test_y = test["target"].to_numpy()

    model.fit(train_x, train_y)
    if spec.tune_threshold:
        val_score = positive_scores(model, val_x)
        threshold, _ = select_threshold(val_y, val_score, cfg.thresholds)
        val_pred = (val_score >= threshold).astype(int)
        test_score = positive_scores(model, test_x)
        test_pred = (test_score >= threshold).astype(int)
    else:
        threshold = None
        val_pred = model.predict(val_x)
        test_pred = model.predict(test_x)
        val_score = positive_scores(model, val_x)
        test_score = positive_scores(model, test_x)

    val_metrics = metrics_from_predictions(val_y, val_pred, val_score)
    test_metrics = metrics_from_predictions(test_y, test_pred, test_score)

    rows = []
    for split, metrics in [("validation", val_metrics), ("test", test_metrics)]:
        row = {"scenario": scenario, "model": spec.name, "split": split, "threshold": threshold}
        row.update(metrics)
        rows.append(row)

    detail = {
        "scenario": scenario,
        "model": spec.name,
        "threshold": threshold,
        "validation": val_metrics,
        "test": test_metrics,
    }
    return rows, detail


def split_counts(frame: pd.DataFrame) -> dict[str, Any]:
    n = int(len(frame))
    positive = int(frame["target"].sum()) if n else 0
    return {
        "n": n,
        "positive": positive,
        "negative": int(n - positive),
        "positive_rate": float(positive / n) if n else 0.0,
    }


def make_original_scenario(data: pd.DataFrame) -> SplitScenario:
    out = data.copy()
    out["eval_split"] = out["split"]
    diagnostics: list[dict[str, Any]] = []
    for split in ["train", "validation", "test"]:
        frame = out[out["eval_split"] == split]
        row = {"scenario": "original_split", "holdout_field": "sample_id", "split": split}
        row.update(split_counts(frame))
        row.update({"group_count": len(frame), "unseen_group_count": 0 if split == "train" else len(frame), "examples": ""})
        diagnostics.append(row)
    return SplitScenario("original_split", out, diagnostics)


def take_groups(
    groups: list[Any],
    group_sizes: dict[Any, int],
    target_size: int,
) -> tuple[set[Any], list[Any]]:
    selected: list[Any] = []
    remaining: list[Any] = []
    total = 0
    for group in groups:
        if total < target_size:
            selected.append(group)
            total += group_sizes[group]
        else:
            remaining.append(group)
    return set(selected), remaining


def group_split_penalty(
    data: pd.DataFrame,
    group_field: str,
    train_groups: set[Any],
    val_groups: set[Any],
    test_groups: set[Any],
    target_train: int,
    target_val: int,
    target_test: int,
) -> float:
    split_frames = {
        "train": data[data[group_field].isin(train_groups)],
        "validation": data[data[group_field].isin(val_groups)],
        "test": data[data[group_field].isin(test_groups)],
    }
    penalty = 0.0
    targets = {"train": target_train, "validation": target_val, "test": target_test}
    overall_rate = float(data["target"].mean())
    for split, frame in split_frames.items():
        counts = split_counts(frame)
        if counts["n"] == 0:
            penalty += 1_000_000.0
            continue
        if split == "train" and (counts["positive"] == 0 or counts["negative"] == 0):
            penalty += 1_000_000.0
        elif counts["positive"] == 0 or counts["negative"] == 0:
            penalty += 10_000.0
        penalty += abs(counts["n"] - targets[split]) / max(len(data), 1)
        penalty += abs(counts["positive_rate"] - overall_rate)
    return penalty


def make_group_holdout_scenario(data: pd.DataFrame, group_field: str, cfg: Config) -> SplitScenario:
    if group_field not in data.columns:
        raise ValueError(f"Missing group field: {group_field}")

    group_sizes = data.groupby(group_field).size().to_dict()
    groups = list(group_sizes)
    target_test = max(1, round(len(data) * cfg.test_fraction))
    target_val = max(1, round(len(data) * cfg.validation_fraction))
    target_train = max(1, len(data) - target_test - target_val)
    rng = np.random.default_rng(cfg.random_seed + sum(ord(ch) for ch in group_field))

    best: tuple[float, set[Any], set[Any], set[Any]] | None = None
    for _ in range(cfg.group_split_trials):
        shuffled = list(rng.permutation(groups))
        test_groups, rest = take_groups(shuffled, group_sizes, target_test)
        val_groups, rest = take_groups(rest, group_sizes, target_val)
        train_groups = set(rest)
        penalty = group_split_penalty(
            data,
            group_field,
            train_groups,
            val_groups,
            test_groups,
            target_train,
            target_val,
            target_test,
        )
        if best is None or penalty < best[0]:
            best = (penalty, train_groups, val_groups, test_groups)

    assert best is not None
    _, train_groups, val_groups, test_groups = best
    train = data[data[group_field].isin(train_groups)].copy()
    if train["target"].nunique() < 2:
        raise RuntimeError(f"Cannot build a valid {group_field} holdout split: train split has one class.")

    out = data.copy()
    out["eval_split"] = "train"
    out.loc[out[group_field].isin(val_groups), "eval_split"] = "validation"
    out.loc[out[group_field].isin(test_groups), "eval_split"] = "test"

    diagnostics: list[dict[str, Any]] = []
    train_values = set(out[out["eval_split"] == "train"][group_field])
    for split in ["train", "validation", "test"]:
        frame = out[out["eval_split"] == split]
        values = sorted(set(frame[group_field]))
        unseen = set(values) - train_values
        row = {
            "scenario": f"{group_field}_holdout",
            "holdout_field": group_field,
            "split": split,
            "group_count": len(values),
            "unseen_group_count": 0 if split == "train" else len(unseen),
            "examples": ", ".join(str(item) for item in sorted(unseen)[:5]) if unseen else "",
        }
        row.update(split_counts(frame))
        diagnostics.append(row)
    return SplitScenario(f"{group_field}_holdout", out, diagnostics)


def build_scenarios(data: pd.DataFrame, cfg: Config) -> list[SplitScenario]:
    scenarios = [make_original_scenario(data)]
    for field in cfg.group_holdout_fields:
        scenarios.append(make_group_holdout_scenario(data, field, cfg))
    return scenarios


def evaluate_scenario(scenario: SplitScenario, cfg: Config) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    train = scenario.data[scenario.data["eval_split"] == "train"].copy()
    val = scenario.data[scenario.data["eval_split"] == "validation"].copy()
    test = scenario.data[scenario.data["eval_split"] == "test"].copy()
    if train.empty or val.empty or test.empty:
        raise RuntimeError(f"Scenario {scenario.name} has empty train/validation/test split.")
    if train["target"].nunique() < 2:
        raise RuntimeError(f"Scenario {scenario.name} train split has one class.")

    metric_rows: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    for spec in build_model_specs(cfg):
        rows, detail = evaluate_model(scenario.name, spec, train, val, test, cfg)
        metric_rows.extend(rows)
        details.append(detail)
    return metric_rows, details


def choose_prediction_model(metrics: pd.DataFrame, cfg: Config) -> str:
    model_names = {spec.name for spec in build_model_specs(cfg)}
    if cfg.prediction_model != "best_group_test":
        if cfg.prediction_model not in model_names:
            raise ValueError(f"Unknown prediction model: {cfg.prediction_model}")
        return cfg.prediction_model

    test = metrics[(metrics["split"] == "test") & (metrics["model"] != "majority")].copy()
    group_test = test[test["scenario"].str.endswith("_holdout")].copy()
    if group_test.empty:
        group_test = test
    grouped = (
        group_test.groupby("model")[["positive_f1", "balanced_accuracy", "macro_f1", "pr_auc"]]
        .mean(numeric_only=True)
        .fillna(-1.0)
        .sort_values(["positive_f1", "balanced_accuracy", "macro_f1", "pr_auc"], ascending=False)
    )
    return str(grouped.index[0])


def choose_prediction_threshold(metrics: pd.DataFrame, model_name: str) -> float:
    thresholds = metrics[
        (metrics["model"] == model_name)
        & (metrics["split"] == "validation")
        & metrics["threshold"].notna()
    ]["threshold"].astype(float)
    if thresholds.empty:
        return 0.5
    return float(np.median(thresholds))


def train_and_predict_full_missing(
    labeled: pd.DataFrame,
    full_missing: pd.DataFrame,
    metrics: pd.DataFrame,
    cfg: Config,
) -> dict[str, Any]:
    model_name = choose_prediction_model(metrics, cfg)
    threshold = choose_prediction_threshold(metrics, model_name)
    specs = {spec.name: spec for spec in build_model_specs(cfg)}
    spec = specs[model_name]
    model = spec.model
    model.fit(select_features(labeled, cfg, spec.feature_view), labeled["target"].to_numpy())
    scores = positive_scores(model, select_features(full_missing, cfg, spec.feature_view))
    pred = (scores >= threshold).astype(int)

    known = labeled[["resource_id", "human_label", "target"]].drop_duplicates("resource_id").rename(
        columns={"human_label": "known_human_label", "target": "known_target"}
    )
    output = full_missing[
        ["resource_id", "original_id", "split", "subject", "topic", "skill", "grade", "category"]
    ].copy()
    output["need_image_probability"] = scores
    output["gate_prediction"] = pred
    output["completion_decision"] = np.where(
        pred == 1,
        "need_completion_accidental_missing",
        "skip_structural_absence",
    )
    output = output.merge(known, on="resource_id", how="left")
    output = output.sort_values(["need_image_probability", "resource_id"], ascending=[False, True])
    cfg.full_prediction_csv.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(cfg.full_prediction_csv, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)

    review_path = cfg.report_dir / "full_missing_review_candidates.csv"
    review_text_cols = ["resource_id", "question", "choices", "hint", "lecture", "solution"]
    review_base = output.merge(full_missing[review_text_cols], on="resource_id", how="left")
    unlabeled_review = review_base[review_base["known_human_label"].isna()].copy()
    high_need = unlabeled_review.nlargest(50, "need_image_probability").copy()
    high_need["review_bucket"] = "high_confidence_need_completion"
    high_skip = unlabeled_review.nsmallest(50, "need_image_probability").copy()
    high_skip["review_bucket"] = "high_confidence_skip"
    uncertain = unlabeled_review.assign(
        threshold_distance=(unlabeled_review["need_image_probability"] - threshold).abs()
    ).nsmallest(50, "threshold_distance")
    uncertain["review_bucket"] = "near_threshold_uncertain"
    review = pd.concat([high_need, high_skip, uncertain], ignore_index=True, sort=False)
    review = review.drop(columns=["threshold_distance"], errors="ignore")
    review.to_csv(review_path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)

    counts = output["completion_decision"].value_counts().to_dict()
    unlabeled = output[output["known_human_label"].isna()]
    unlabeled_counts = unlabeled["completion_decision"].value_counts().to_dict()
    quantiles = output["need_image_probability"].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).to_dict()
    return {
        "model": model_name,
        "threshold": threshold,
        "prediction_csv": str(cfg.full_prediction_csv),
        "review_csv": str(review_path),
        "total_missing": int(len(output)),
        "labeled_source_count": int(output["known_human_label"].notna().sum()),
        "unlabeled_missing_count": int(output["known_human_label"].isna().sum()),
        "decision_counts": {str(k): int(v) for k, v in counts.items()},
        "unlabeled_decision_counts": {str(k): int(v) for k, v in unlabeled_counts.items()},
        "probability_quantiles": {str(k): float(v) for k, v in quantiles.items()},
    }


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)
    return value


def format_float(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if np.isnan(value):
            return ""
        return f"{value:.4f}"
    return str(value)


def md_table(frame: pd.DataFrame, columns: list[str]) -> str:
    rows = ["| " + " | ".join(columns) + " |"]
    rows.append("| " + " | ".join("---" for _ in columns) + " |")
    for _, row in frame[columns].iterrows():
        rows.append("| " + " | ".join(format_float(row[col]) for col in columns) + " |")
    return "\n".join(rows)


def write_summary(
    report_dir: Path,
    metrics: pd.DataFrame,
    details: list[dict[str, Any]],
    labeled: pd.DataFrame,
    split_diagnostics: pd.DataFrame,
    prediction_summary: dict[str, Any],
    cfg: Config,
) -> None:
    label_counts = labeled["human_label"].value_counts().to_dict()
    target_counts = labeled["target"].value_counts().to_dict()
    positive_text = " OR ".join(cfg.positive_labels)

    metric_cols = [
        "scenario",
        "model",
        "split",
        "threshold",
        "n",
        "positive_rate",
        "balanced_accuracy",
        "macro_f1",
        "positive_f1",
        "positive_precision",
        "positive_recall",
        "pr_auc",
        "tn",
        "fp",
        "fn",
        "tp",
    ]
    diagnostic_cols = [
        "scenario",
        "holdout_field",
        "split",
        "n",
        "positive",
        "negative",
        "positive_rate",
        "group_count",
        "unseen_group_count",
        "examples",
    ]
    test = metrics[metrics["split"] == "test"].copy()
    best_by_scenario = (
        test.sort_values(["scenario", "positive_f1", "balanced_accuracy", "macro_f1"], ascending=[True, False, False, False])
        .groupby("scenario")
        .head(1)
    )
    best_cols = ["scenario", "model", "n", "positive_f1", "balanced_accuracy", "macro_f1", "pr_auc", "tn", "fp", "fn", "tp"]

    summary = [
        "# Exp0.2 选择性补全门控基线",
        "",
        "目标：",
        "",
        "```text",
        "0 = structural_absence",
        f"1 = image_needed_missing = {positive_text}",
        "```",
        "",
        "## 数据",
        "",
        f"- ScienceQA 全量样本：21,208 条。",
        f"- ScienceQA 缺图样本：10,876 条。",
        f"- 当前有真值标签的缺图样本：{len(labeled)} 条。",
        f"- 标签计数：`{json.dumps(label_counts, ensure_ascii=False, sort_keys=True)}`。",
        f"- 目标计数：`{json.dumps({str(k): int(v) for k, v in target_counts.items()}, ensure_ascii=False, sort_keys=True)}`。",
        "",
        "## 评测设计",
        "",
        "- `original_split`：沿用 ScienceQA 原始 train / validation / test 样本划分，测试模型是否见过同一条样本。",
        "- `topic_holdout`：按 topic 分组划分，validation / test 的 topic 不出现在训练集中。",
        "- `skill_holdout`：按 skill 分组划分，validation / test 的 skill 不出现在训练集中。",
        "",
        "## 分组划分诊断",
        "",
        md_table(split_diagnostics, diagnostic_cols),
        "",
        "## 测试集最佳结果",
        "",
        md_table(best_by_scenario, best_cols),
        "",
        "## 全部指标",
        "",
        md_table(metrics, metric_cols),
        "",
        "## 全量缺图预测",
        "",
        f"- 预测模型：`{prediction_summary['model']}`。",
        f"- 使用阈值：`{prediction_summary['threshold']:.4f}`。",
        f"- 输出文件：`{prediction_summary['prediction_csv']}`。",
        f"- 人工复核清单：`{prediction_summary['review_csv']}`。",
        f"- 全量缺图样本：{prediction_summary['total_missing']} 条。",
        f"- 其中已有人工标签来源样本：{prediction_summary['labeled_source_count']} 条。",
        f"- 其余未标注缺图样本：{prediction_summary['unlabeled_missing_count']} 条。",
        f"- 全量预测计数：`{json.dumps(prediction_summary['decision_counts'], ensure_ascii=False, sort_keys=True)}`。",
        f"- 未标注样本预测计数：`{json.dumps(prediction_summary['unlabeled_decision_counts'], ensure_ascii=False, sort_keys=True)}`。",
        f"- 概率分位数：`{json.dumps(prediction_summary['probability_quantiles'], ensure_ascii=False, sort_keys=True)}`。",
        "",
        "## 结果解读",
        "",
        "- 372 条候选样本不是全量数据；真正有二分类真值的缺图样本是 322 条。",
        "- 原始划分只能说明模型没有见过同一条样本，不能排除 topic / skill 记忆效应。",
        "- 分组留出结果用于判断模型能否泛化到未见过的 topic 或 skill。",
        "- 全量缺图预测是伪标签和排序清单，不能直接当作准确率；写入论文前应继续抽查高置信正类和高置信负类。",
        "",
    ]
    (report_dir / "run_summary.md").write_text("\n".join(summary), encoding="utf-8")
    (report_dir / "model_details.json").write_text(
        json.dumps(json_safe({"models": details, "full_prediction": prediction_summary}), ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/exp0_2_selective_completion_gate.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    cfg.report_dir.mkdir(parents=True, exist_ok=True)

    labeled = prepare_labeled_data(cfg)
    scenarios = build_scenarios(labeled, cfg)

    metric_rows: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, Any]] = []
    for scenario in scenarios:
        rows, scenario_details = evaluate_scenario(scenario, cfg)
        metric_rows.extend(rows)
        details.extend(scenario_details)
        diagnostic_rows.extend(scenario.diagnostics)

    metrics = pd.DataFrame(metric_rows)
    split_diagnostics = pd.DataFrame(diagnostic_rows)
    metrics.to_csv(cfg.report_dir / "metrics.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    split_diagnostics.to_csv(cfg.report_dir / "split_diagnostics.csv", index=False, quoting=csv.QUOTE_MINIMAL)

    full_missing = prepare_full_missing_resources(cfg)
    prediction_summary = train_and_predict_full_missing(labeled, full_missing, metrics, cfg)
    write_summary(cfg.report_dir, metrics, details, labeled, split_diagnostics, prediction_summary, cfg)
    print(f"Wrote {cfg.report_dir}")
    print(f"Wrote {cfg.full_prediction_csv}")


if __name__ == "__main__":
    main()
