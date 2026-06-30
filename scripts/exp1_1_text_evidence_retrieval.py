"""Exp1.1 教育图文证据对齐检索的文本证据 baseline。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


DEFAULT_CONFIG: dict[str, Any] = {
    "paths": {
        "report_dir": "reports/exp1_1_text_evidence_retrieval",
        "input_samples": [
            "data/educational_mm/schema_samples/scienceqa_schema_sample.csv",
            "data/educational_mm/schema_samples/tqa_ck12_schema_sample.csv",
            "data/educational_mm/schema_samples/ai2d_schema_sample.csv",
        ],
    },
    "retrieval": {
        "query_columns": ["question", "choices", "topic", "skill"],
        "evidence_column": "text_context",
        "min_evidence_chars": 5,
        "top_k": [1, 5, 10],
        "max_failure_examples": 20,
    },
    "models": {
        "tfidf": {"ngram_range": [1, 2], "min_df": 1, "max_features": 20000},
        "bm25": {"k1": 1.5, "b": 0.75},
    },
}


@dataclass
class Config:
    report_dir: Path
    input_samples: list[Path]
    query_columns: list[str]
    evidence_column: str
    min_evidence_chars: int
    top_k: list[int]
    max_failure_examples: int
    tfidf_ngram_range: tuple[int, int]
    tfidf_min_df: int
    tfidf_max_features: int
    bm25_k1: float
    bm25_b: float


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

    retrieval = raw["retrieval"]
    tfidf = raw["models"]["tfidf"]
    bm25 = raw["models"]["bm25"]
    ngram_range = tuple(int(x) for x in tfidf["ngram_range"])
    return Config(
        report_dir=Path(raw["paths"]["report_dir"]),
        input_samples=[Path(p) for p in raw["paths"]["input_samples"]],
        query_columns=list(retrieval["query_columns"]),
        evidence_column=str(retrieval["evidence_column"]),
        min_evidence_chars=int(retrieval["min_evidence_chars"]),
        top_k=sorted(int(k) for k in retrieval["top_k"]),
        max_failure_examples=int(retrieval["max_failure_examples"]),
        tfidf_ngram_range=(ngram_range[0], ngram_range[1]),
        tfidf_min_df=int(tfidf["min_df"]),
        tfidf_max_features=int(tfidf["max_features"]),
        bm25_k1=float(bm25["k1"]),
        bm25_b=float(bm25["b"]),
    )


def normalize_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split())


def make_query(row: pd.Series, columns: list[str]) -> str:
    parts = []
    for column in columns:
        value = normalize_text(row.get(column, ""))
        if value:
            parts.append(value)
    return " ".join(parts)


def evidence_id(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def load_samples(paths: list[Path], cfg: Config) -> pd.DataFrame:
    frames = []
    for path in paths:
        data = pd.read_csv(path)
        data["source_file"] = str(path)
        frames.append(data)
    data = pd.concat(frames, ignore_index=True, sort=False)
    data["query_text"] = data.apply(lambda row: make_query(row, cfg.query_columns), axis=1)
    data["evidence_text"] = data[cfg.evidence_column].map(normalize_text)
    data["evidence_id"] = data["evidence_text"].map(evidence_id)
    data["dataset"] = data["dataset"].fillna("unknown").astype(str)
    data["sample_id"] = data["sample_id"].fillna("").astype(str)
    return data


def prepare_dataset(data: pd.DataFrame, dataset: str, cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    subset = data[data["dataset"] == dataset].copy()
    eval_rows = subset[subset["evidence_text"].str.len() >= cfg.min_evidence_chars].copy()
    corpus = (
        eval_rows[["evidence_id", "evidence_text"]]
        .drop_duplicates("evidence_id")
        .reset_index(drop=True)
    )
    return eval_rows.reset_index(drop=True), corpus


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def bm25_scores(
    query: str,
    tokenized_docs: list[list[str]],
    doc_freq: Counter[str],
    avgdl: float,
    k1: float,
    b: float,
) -> np.ndarray:
    query_terms = tokenize(query)
    if not query_terms or not tokenized_docs:
        return np.zeros(len(tokenized_docs), dtype=float)
    n_docs = len(tokenized_docs)
    scores = np.zeros(n_docs, dtype=float)
    query_counts = Counter(query_terms)
    for term, qf in query_counts.items():
        df = doc_freq.get(term, 0)
        if df == 0:
            continue
        idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
        for idx, doc in enumerate(tokenized_docs):
            tf = doc.count(term)
            if tf == 0:
                continue
            dl = len(doc)
            denom = tf + k1 * (1 - b + b * dl / avgdl) if avgdl else tf + k1
            scores[idx] += idf * (tf * (k1 + 1) / denom) * qf
    return scores


def rank_from_scores(scores: np.ndarray) -> np.ndarray:
    # Stable sort by score desc, then index asc for reproducibility.
    return np.lexsort((np.arange(len(scores)), -scores))


def rank_tfidf(eval_rows: pd.DataFrame, corpus: pd.DataFrame, cfg: Config) -> list[np.ndarray]:
    vectorizer = TfidfVectorizer(
        ngram_range=cfg.tfidf_ngram_range,
        min_df=cfg.tfidf_min_df,
        max_features=cfg.tfidf_max_features,
        strip_accents="unicode",
    )
    corpus_matrix = vectorizer.fit_transform(corpus["evidence_text"])
    query_matrix = vectorizer.transform(eval_rows["query_text"])
    sims = cosine_similarity(query_matrix, corpus_matrix)
    return [rank_from_scores(row) for row in sims]


def rank_bm25(eval_rows: pd.DataFrame, corpus: pd.DataFrame, cfg: Config) -> list[np.ndarray]:
    tokenized_docs = [tokenize(text) for text in corpus["evidence_text"]]
    doc_freq: Counter[str] = Counter()
    for doc in tokenized_docs:
        doc_freq.update(set(doc))
    avgdl = float(np.mean([len(doc) for doc in tokenized_docs])) if tokenized_docs else 0.0
    rankings = []
    for query in eval_rows["query_text"]:
        scores = bm25_scores(query, tokenized_docs, doc_freq, avgdl, cfg.bm25_k1, cfg.bm25_b)
        rankings.append(rank_from_scores(scores))
    return rankings


def evaluate_rankings(
    dataset: str,
    model: str,
    eval_rows: pd.DataFrame,
    corpus: pd.DataFrame,
    rankings: list[np.ndarray],
    cfg: Config,
) -> tuple[dict[str, Any], list[dict[str, Any]], pd.DataFrame]:
    corpus_ids = corpus["evidence_id"].tolist()
    max_k = max(cfg.top_k)
    hits = {k: 0 for k in cfg.top_k}
    rr_sum = 0.0
    rank_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for row_idx, (_, row) in enumerate(eval_rows.iterrows()):
        ranking = rankings[row_idx]
        ranked_ids = [corpus_ids[idx] for idx in ranking]
        target = row["evidence_id"]
        rank = ranked_ids.index(target) + 1 if target in ranked_ids else None
        if rank is not None:
            rr_sum += 1.0 / rank
            for k in cfg.top_k:
                if rank <= k:
                    hits[k] += 1
        top_indices = ranking[:max_k]
        top_ids = [corpus_ids[idx] for idx in top_indices]
        rank_rows.append(
            {
                "dataset": dataset,
                "model": model,
                "sample_id": row["sample_id"],
                "target_evidence_id": target,
                "rank": rank,
                "top_evidence_ids": json.dumps(top_ids, ensure_ascii=False),
            }
        )
        if (rank is None or rank > 1) and len(failures) < cfg.max_failure_examples:
            best_idx = int(ranking[0]) if len(ranking) else -1
            failures.append(
                {
                    "dataset": dataset,
                    "model": model,
                    "sample_id": row["sample_id"],
                    "rank": rank,
                    "question": row["question"],
                    "target_evidence": row["evidence_text"][:500],
                    "top_evidence": corpus.iloc[best_idx]["evidence_text"][:500] if best_idx >= 0 else "",
                }
            )

    n = len(eval_rows)
    metrics: dict[str, Any] = {
        "dataset": dataset,
        "model": model,
        "n_queries": n,
        "n_corpus": len(corpus),
        "mrr": rr_sum / n if n else 0.0,
    }
    for k in cfg.top_k:
        metrics[f"recall_at_{k}"] = hits[k] / n if n else 0.0
    return metrics, failures, pd.DataFrame(rank_rows)


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


def write_summary(
    cfg: Config,
    data: pd.DataFrame,
    metrics: pd.DataFrame,
    skipped: list[dict[str, Any]],
    failures: pd.DataFrame,
) -> None:
    cfg.report_dir.mkdir(parents=True, exist_ok=True)
    metric_view = metrics.copy()
    for col in metric_view.columns:
        if metric_view[col].dtype.kind == "f":
            metric_view[col] = metric_view[col].map(format_float)
    dataset_rows = []
    for dataset, frame in data.groupby("dataset"):
        text_count = int((frame["evidence_text"].str.len() >= cfg.min_evidence_chars).sum())
        dataset_rows.append(
            {
                "dataset": dataset,
                "samples": len(frame),
                "text_evidence_queries": text_count,
                "has_image": int(frame["has_image"].sum()),
            }
        )
    lines = [
        "# Exp1.1 文本证据对齐检索 Baseline",
        "",
        "## 目标",
        "",
        "在统一教育多模态 schema 上，先验证最小文本证据检索任务是否可运行：给定题目和选项，检索对应的 `text_context` 证据。",
        "",
        "当前实验只评估文本证据。AI2D 当前 schema 样例没有 `text_context`，因此不参与文本检索；后续进入图像/diagram 证据检索。",
        "",
        "## 数据覆盖",
        "",
        df_to_markdown(pd.DataFrame(dataset_rows)),
        "",
        "## 指标",
        "",
        df_to_markdown(metric_view),
        "",
    ]
    if skipped:
        lines.extend(["## 跳过的数据集", "", df_to_markdown(pd.DataFrame(skipped)), ""])
    if not failures.empty:
        lines.extend(
            [
                "## 失败样例",
                "",
                "以下样例用于观察当前文本检索 baseline 的主要错误模式。",
                "",
                df_to_markdown(failures.head(cfg.max_failure_examples)),
                "",
            ]
        )
    lines.extend(
        [
            "## 结果解读",
            "",
            "- 该实验是 RC1 的最小可运行 baseline，不代表最终模型。",
            "- ScienceQA 的 `text_context` 来自 hint / lecture / solution，文本证据较丰富。",
            "- TQA / CK12 当前使用公开 instruction 版，`text_context` 主要是 lesson + instruction，缺少官方完整教材段落，因此检索结果只能作为 schema 连通性测试。",
            "- AI2D 需要转入图像/diagram 证据检索，不能用当前文本 baseline 评价。",
            "",
            "## 下一步",
            "",
            "1. 为 ScienceQA / TQA 构造 same-topic 和 same-skill hard negative。",
            "2. 为 AI2D 构造 wrong-image hard negative，并实现 CLIP/SigLIP 图文证据检索。",
            "3. 将 TF-IDF/BM25 扩展为 Sentence-BERT 文本检索 baseline。",
            "",
        ]
    )
    (cfg.report_dir / "run_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/exp1_1_text_evidence_retrieval.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    cfg.report_dir.mkdir(parents=True, exist_ok=True)

    data = load_samples(cfg.input_samples, cfg)
    metric_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    rank_frames: list[pd.DataFrame] = []
    skipped: list[dict[str, Any]] = []

    for dataset in sorted(data["dataset"].unique()):
        eval_rows, corpus = prepare_dataset(data, dataset, cfg)
        if eval_rows.empty or len(corpus) < 2:
            skipped.append(
                {
                    "dataset": dataset,
                    "reason": "文本证据为空或候选证据少于 2 条",
                    "n_queries": len(eval_rows),
                    "n_corpus": len(corpus),
                }
            )
            continue

        model_rankings = {
            "tfidf": rank_tfidf(eval_rows, corpus, cfg),
            "bm25": rank_bm25(eval_rows, corpus, cfg),
        }
        for model, rankings in model_rankings.items():
            metrics, failures, ranks = evaluate_rankings(dataset, model, eval_rows, corpus, rankings, cfg)
            metric_rows.append(metrics)
            failure_rows.extend(failures)
            rank_frames.append(ranks)

    metrics = pd.DataFrame(metric_rows)
    failures = pd.DataFrame(failure_rows)
    ranks = pd.concat(rank_frames, ignore_index=True, sort=False) if rank_frames else pd.DataFrame()
    metrics.to_csv(cfg.report_dir / "metrics.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    failures.to_csv(cfg.report_dir / "failure_examples.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    ranks.to_csv(cfg.report_dir / "query_rankings.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    write_summary(cfg, data, metrics, skipped, failures)
    print(f"Wrote {cfg.report_dir}")


if __name__ == "__main__":
    main()
