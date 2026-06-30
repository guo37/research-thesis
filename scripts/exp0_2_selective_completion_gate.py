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
        "report_dir": "reports/exp0_2_selective_completion_gate",
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
}


@dataclass
class Config:
    input_csv: Path
    report_dir: Path
    negative_label: str
    positive_labels: list[str]
    categorical: list[str]
    numeric: list[str]
    text: list[str]
    random_seed: int
    max_text_features: int
    thresholds: list[float]


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
    return Config(
        input_csv=Path(raw["paths"]["input_csv"]),
        report_dir=Path(raw["paths"]["report_dir"]),
        negative_label=str(raw["target"]["negative_label"]),
        positive_labels=list(raw["target"]["positive_labels"]),
        categorical=list(raw["features"]["categorical"]),
        numeric=list(raw["features"]["numeric"]),
        text=list(raw["features"]["text"]),
        random_seed=int(raw["model"]["random_seed"]),
        max_text_features=int(raw["model"]["max_text_features"]),
        thresholds=[round(float(x), 4) for x in thresholds],
    )


def prepare_data(cfg: Config) -> pd.DataFrame:
    data = pd.read_csv(cfg.input_csv)
    data = data[data["has_image"].astype(str) == "0"].copy()
    keep_labels = {cfg.negative_label, *cfg.positive_labels}
    data = data[data["human_label"].isin(keep_labels)].copy()
    data["target"] = data["human_label"].isin(cfg.positive_labels).astype(int)
    data["text_bundle"] = data[cfg.text].fillna("").astype(str).agg(" ".join, axis=1)
    for col in cfg.categorical:
        data[col] = data[col].fillna("<missing>").astype(str)
    for col in cfg.numeric:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    return data


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


def metrics_from_predictions(y_true: np.ndarray, y_pred: np.ndarray, score: np.ndarray | None = None) -> dict[str, Any]:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    out: dict[str, Any] = {
        "n": int(len(y_true)),
        "positive_rate": float(np.mean(y_true)) if len(y_true) else 0.0,
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "positive_f1": f1_score(y_true, y_pred, pos_label=1, zero_division=0),
        "positive_precision": precision_score(y_true, y_pred, pos_label=1, zero_division=0),
        "positive_recall": recall_score(y_true, y_pred, pos_label=1, zero_division=0),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }
    if score is not None and len(set(y_true)) == 2:
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
        key = (current["positive_f1"], current["balanced_accuracy"], current["macro_f1"])
        best_key = (best_metrics["positive_f1"], best_metrics["balanced_accuracy"], best_metrics["macro_f1"])
        if key > best_key:
            best_threshold = threshold
            best_metrics = current
    assert best_metrics is not None
    return best_threshold, best_metrics


def evaluate_model(
    name: str,
    model: Any,
    train_x: Any,
    train_y: np.ndarray,
    val_x: Any,
    val_y: np.ndarray,
    test_x: Any,
    test_y: np.ndarray,
    thresholds: list[float],
    tune_threshold: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    model.fit(train_x, train_y)
    if tune_threshold:
        val_score = positive_scores(model, val_x)
        threshold, val_metrics = select_threshold(val_y, val_score, thresholds)
        test_score = positive_scores(model, test_x)
        test_pred = (test_score >= threshold).astype(int)
        test_metrics = metrics_from_predictions(test_y, test_pred, test_score)
        val_pred = (val_score >= threshold).astype(int)
        val_metrics = metrics_from_predictions(val_y, val_pred, val_score)
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
        row = {"model": name, "split": split, "threshold": threshold}
        row.update(metrics)
        rows.append(row)

    detail = {
        "model": name,
        "threshold": threshold,
        "validation": val_metrics,
        "test": test_metrics,
    }
    return rows, detail


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


def split_overlap_rows(data: pd.DataFrame, fields: list[str]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    train = data[data["split"] == "train"]
    for field in fields:
        train_values = set(train[field].fillna("<missing>").astype(str))
        for split in ["validation", "test"]:
            split_values = set(data[data["split"] == split][field].fillna("<missing>").astype(str))
            unseen = split_values - train_values
            rows.append(
                [
                    field,
                    split,
                    len(split_values),
                    len(unseen),
                    ", ".join(sorted(unseen)[:5]) if unseen else "",
                ]
            )
    return rows


def write_summary(
    report_dir: Path,
    metrics: pd.DataFrame,
    details: list[dict[str, Any]],
    data: pd.DataFrame,
    cfg: Config,
) -> None:
    test = metrics[metrics["split"] == "test"].sort_values(["positive_f1", "pr_auc"], ascending=False)
    best = test.iloc[0].to_dict()
    label_counts = data["human_label"].value_counts().to_dict()
    target_counts = data["target"].value_counts().to_dict()
    positive_text = " OR ".join(cfg.positive_labels)

    metric_cols = [
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

    def md_table(frame: pd.DataFrame) -> str:
        rows = ["| " + " | ".join(metric_cols) + " |"]
        rows.append("| " + " | ".join("---" for _ in metric_cols) + " |")
        for _, row in frame[metric_cols].iterrows():
            rows.append("| " + " | ".join(format_float(row[col]) for col in metric_cols) + " |")
        return "\n".join(rows)

    overlap_headers = ["字段", "数据划分", "唯一值数量", "训练集中未见值数量", "示例"]
    overlap_rows = split_overlap_rows(data, ["topic", "skill"])
    overlap_table = ["| " + " | ".join(overlap_headers) + " |"]
    overlap_table.append("| " + " | ".join("---" for _ in overlap_headers) + " |")
    for row in overlap_rows:
        overlap_table.append("| " + " | ".join(str(cell) for cell in row) + " |")

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
        f"- 使用样本：{len(data)} 条已标注缺图候选样本。",
        f"- 标签计数：`{json.dumps(label_counts, ensure_ascii=False, sort_keys=True)}`。",
        f"- 目标计数：`{json.dumps({str(k): int(v) for k, v in target_counts.items()}, ensure_ascii=False, sort_keys=True)}`。",
        "",
        "## 指标",
        "",
        md_table(metrics),
        "",
        "## 划分重叠检查",
        "",
        "\n".join(overlap_table),
        "",
        "如果验证集/测试集中的 topic 或 skill 大多已经出现在训练集中，高分可能部分来自 topic/skill 记忆效应。作为论文证据前，需要增加分组压力测试。",
        "",
        "## 当前最佳测试结果",
        "",
        f"- 按正类 F1 选择的最佳模型：`{best['model']}`。",
        f"- 正类 F1：`{best['positive_f1']:.4f}`。",
        f"- PR-AUC：`{best['pr_auc']:.4f}`。",
        f"- Balanced accuracy：`{best['balanced_accuracy']:.4f}`。",
        f"- 测试集混淆矩阵：TN={int(best['tn'])}, FP={int(best['fp'])}, FN={int(best['fn'])}, TP={int(best['tp'])}。",
        "",
        "## 结果解读",
        "",
        "- 当前标注集较小，因此该结果是可行性信号，还不是最终论文证据。",
        "- 结果支持将 RC2 表述为模态必要性门控：跳过结构性无图，处理意外缺图。",
        "- 如果标签包含自动辅助过程，在写入论文前应抽查正类样本。",
        "",
    ]
    (report_dir / "run_summary.md").write_text("\n".join(summary), encoding="utf-8")
    (report_dir / "model_details.json").write_text(
        json.dumps(json_safe(details), ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/exp0_2_selective_completion_gate.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    cfg.report_dir.mkdir(parents=True, exist_ok=True)

    data = prepare_data(cfg)
    train = data[data["split"] == "train"].copy()
    val = data[data["split"] == "validation"].copy()
    test = data[data["split"] == "test"].copy()
    if train.empty or val.empty or test.empty:
        raise RuntimeError("Expected non-empty train, validation, and test splits.")

    y_train = train["target"].to_numpy()
    y_val = val["target"].to_numpy()
    y_test = test["target"].to_numpy()

    x_meta_train = train[cfg.categorical + cfg.numeric]
    x_meta_val = val[cfg.categorical + cfg.numeric]
    x_meta_test = test[cfg.categorical + cfg.numeric]

    models = [
        ("majority", DummyClassifier(strategy="most_frequent"), train[cfg.categorical], val[cfg.categorical], test[cfg.categorical], False),
        ("metadata", build_metadata_model(cfg), x_meta_train, x_meta_val, x_meta_test, True),
        ("text", build_text_model(cfg), train["text_bundle"], val["text_bundle"], test["text_bundle"], True),
        ("metadata_text", build_metadata_text_model(cfg), train, val, test, True),
    ]

    metric_rows: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    for name, model, train_x, val_x, test_x, tune_threshold in models:
        rows, detail = evaluate_model(
            name,
            model,
            train_x,
            y_train,
            val_x,
            y_val,
            test_x,
            y_test,
            cfg.thresholds,
            tune_threshold=tune_threshold,
        )
        metric_rows.extend(rows)
        details.append(detail)

    metrics = pd.DataFrame(metric_rows)
    metrics.to_csv(cfg.report_dir / "metrics.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    write_summary(cfg.report_dir, metrics, details, data, cfg)
    print(f"Wrote {cfg.report_dir}")


if __name__ == "__main__":
    main()
