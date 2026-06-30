"""Exp1.2 RC1 hard negative 与 wrong-image 候选构造。

本实验复用 Exp1.1 的 TF-IDF / BM25 文本检索 baseline，但把评测候选池
限制为 positive evidence + 教育元数据约束的 hard negatives。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


DEFAULT_CONFIG: dict[str, Any] = {
    "paths": {
        "report_dir": "reports/exp1_2_hard_negative_retrieval",
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
        "max_failure_examples": 30,
    },
    "hard_negatives": {
        "strategies": ["random", "same_subject", "same_topic", "same_skill"],
        "min_negatives_per_query": 1,
        "max_negatives_per_query": 20,
        "random_seed": 42,
    },
    "wrong_image": {
        "dataset": "ai2d",
        "strategies": [
            "random_wrong_image",
            "lexical_wrong_image",
            "same_topic_wrong_image",
            "same_skill_wrong_image",
        ],
        "max_negatives_per_query": 5,
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
    strategies: list[str]
    min_negatives_per_query: int
    max_negatives_per_query: int
    random_seed: int
    wrong_image_dataset: str
    wrong_image_strategies: list[str]
    wrong_image_max_negatives_per_query: int
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
            print("PyYAML is not installed; using the built-in default Exp1.2 config.", file=sys.stderr)
        else:
            with open(path, "r", encoding="utf-8") as f:
                raw = deep_update(DEFAULT_CONFIG, yaml.safe_load(f) or {})

    retrieval = raw["retrieval"]
    hard_negatives = raw["hard_negatives"]
    wrong_image = raw["wrong_image"]
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
        strategies=list(hard_negatives["strategies"]),
        min_negatives_per_query=int(hard_negatives["min_negatives_per_query"]),
        max_negatives_per_query=int(hard_negatives["max_negatives_per_query"]),
        random_seed=int(hard_negatives["random_seed"]),
        wrong_image_dataset=str(wrong_image["dataset"]),
        wrong_image_strategies=list(wrong_image["strategies"]),
        wrong_image_max_negatives_per_query=int(wrong_image["max_negatives_per_query"]),
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
    for column in ["dataset", "sample_id", "subject", "topic", "skill", "image_ref"]:
        data[column] = data[column].fillna("").astype(str)
    data["has_image"] = pd.to_numeric(data["has_image"], errors="coerce").fillna(0).astype(int)
    return data


def prepare_text_dataset(data: pd.DataFrame, dataset: str, cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    subset = data[data["dataset"] == dataset].copy()
    eval_rows = subset[subset["evidence_text"].str.len() >= cfg.min_evidence_chars].copy()
    corpus = (
        eval_rows[["evidence_id", "evidence_text", "dataset", "subject", "topic", "skill", "sample_id"]]
        .drop_duplicates("evidence_id")
        .reset_index(drop=True)
    )
    return eval_rows.reset_index(drop=True), corpus


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def term_ngrams(tokens: list[str], ngram_range: tuple[int, int]) -> list[str]:
    terms: list[str] = []
    min_n, max_n = ngram_range
    for n in range(min_n, max_n + 1):
        if n <= 0 or len(tokens) < n:
            continue
        terms.extend(" ".join(tokens[idx : idx + n]) for idx in range(0, len(tokens) - n + 1))
    return terms


def text_terms(text: str, ngram_range: tuple[int, int]) -> list[str]:
    return term_ngrams(tokenize(text), ngram_range)


def build_tfidf_vocab(texts: list[str], cfg: Config) -> tuple[dict[str, int], Counter[str]]:
    doc_freq: Counter[str] = Counter()
    for text in texts:
        doc_freq.update(set(text_terms(text, cfg.tfidf_ngram_range)))
    terms = [term for term, df in doc_freq.items() if df >= cfg.tfidf_min_df]
    terms = sorted(terms, key=lambda term: (-doc_freq[term], term))
    if cfg.tfidf_max_features > 0:
        terms = terms[: cfg.tfidf_max_features]
    return {term: idx for idx, term in enumerate(terms)}, doc_freq


def transform_tfidf(
    texts: list[str],
    vocab: dict[str, int],
    doc_freq: Counter[str],
    n_docs: int,
    cfg: Config,
) -> np.ndarray:
    matrix = np.zeros((len(texts), len(vocab)), dtype=float)
    if not vocab:
        return matrix
    idf = np.ones(len(vocab), dtype=float)
    for term, idx in vocab.items():
        idf[idx] = math.log((1 + n_docs) / (1 + doc_freq.get(term, 0))) + 1
    for row_idx, text in enumerate(texts):
        counts = Counter(text_terms(text, cfg.tfidf_ngram_range))
        for term, count in counts.items():
            col_idx = vocab.get(term)
            if col_idx is not None:
                matrix[row_idx, col_idx] = count * idf[col_idx]
    norms = np.linalg.norm(matrix, axis=1)
    nonzero = norms > 0
    matrix[nonzero] = matrix[nonzero] / norms[nonzero, None]
    return matrix


def fit_transform_tfidf(
    corpus_texts: list[str],
    query_texts: list[str],
    cfg: Config,
) -> tuple[np.ndarray, np.ndarray]:
    vocab, doc_freq = build_tfidf_vocab(corpus_texts, cfg)
    corpus_matrix = transform_tfidf(corpus_texts, vocab, doc_freq, len(corpus_texts), cfg)
    query_matrix = transform_tfidf(query_texts, vocab, doc_freq, len(corpus_texts), cfg)
    return corpus_matrix, query_matrix


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


def score_tfidf(eval_rows: pd.DataFrame, corpus: pd.DataFrame, cfg: Config) -> np.ndarray:
    corpus_matrix, query_matrix = fit_transform_tfidf(
        corpus["evidence_text"].tolist(),
        eval_rows["query_text"].tolist(),
        cfg,
    )
    return query_matrix @ corpus_matrix.T


def score_bm25(eval_rows: pd.DataFrame, corpus: pd.DataFrame, cfg: Config) -> np.ndarray:
    tokenized_docs = [tokenize(text) for text in corpus["evidence_text"]]
    doc_freq: Counter[str] = Counter()
    for doc in tokenized_docs:
        doc_freq.update(set(doc))
    avgdl = float(np.mean([len(doc) for doc in tokenized_docs])) if tokenized_docs else 0.0
    rows = [
        bm25_scores(query, tokenized_docs, doc_freq, avgdl, cfg.bm25_k1, cfg.bm25_b)
        for query in eval_rows["query_text"]
    ]
    return np.vstack(rows) if rows else np.empty((0, len(corpus)))


def stable_sample(indices: list[int], limit: int, key: str, seed: int) -> list[int]:
    if len(indices) <= limit:
        return sorted(indices)
    ranked = sorted(
        indices,
        key=lambda idx: hashlib.sha1(f"{seed}|{key}|{idx}".encode("utf-8")).hexdigest(),
    )
    return sorted(ranked[:limit])


def negative_indices(
    strategy: str,
    row: pd.Series,
    corpus: pd.DataFrame,
    target_idx: int,
    row_key: str,
    cfg: Config,
) -> list[int]:
    mask = corpus.index.to_series() != target_idx
    if strategy == "random":
        pass
    elif strategy == "same_subject":
        value = normalize_text(row.get("subject", ""))
        mask &= corpus["subject"] == value
        mask &= value != ""
    elif strategy == "same_topic":
        value = normalize_text(row.get("topic", ""))
        mask &= corpus["topic"] == value
        mask &= value != ""
    elif strategy == "same_skill":
        value = normalize_text(row.get("skill", ""))
        mask &= corpus["skill"] == value
        mask &= value != ""
    elif strategy == "same_topic_diff_skill":
        topic = normalize_text(row.get("topic", ""))
        skill = normalize_text(row.get("skill", ""))
        mask &= corpus["topic"] == topic
        mask &= corpus["skill"] != skill
        mask &= topic != ""
    else:
        raise ValueError(f"Unknown hard-negative strategy: {strategy}")
    indices = [int(idx) for idx in corpus.index[mask]]
    return stable_sample(indices, cfg.max_negatives_per_query, f"{strategy}|{row_key}", cfg.random_seed)


def rank_candidate_pool(scores: np.ndarray, candidate_indices: list[int]) -> list[int]:
    return sorted(candidate_indices, key=lambda idx: (-float(scores[idx]), idx))


def evaluate_hard_negatives(
    dataset: str,
    model: str,
    eval_rows: pd.DataFrame,
    corpus: pd.DataFrame,
    score_matrix: np.ndarray,
    cfg: Config,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], pd.DataFrame]:
    evidence_to_idx = {evidence_id_: idx for idx, evidence_id_ in enumerate(corpus["evidence_id"])}
    metric_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    ranking_rows: list[dict[str, Any]] = []

    for strategy in cfg.strategies:
        ranks: list[int] = []
        margins: list[float] = []
        negative_counts: list[int] = []
        hits = {k: 0 for k in cfg.top_k}
        skipped = 0

        for row_idx, row in eval_rows.iterrows():
            target_idx = evidence_to_idx.get(row["evidence_id"])
            if target_idx is None:
                skipped += 1
                continue
            row_key = f"{dataset}|{row['sample_id']}|{row_idx}"
            negatives = negative_indices(strategy, row, corpus, target_idx, row_key, cfg)
            if len(negatives) < cfg.min_negatives_per_query:
                skipped += 1
                continue

            candidates = [target_idx] + negatives
            ordered = rank_candidate_pool(score_matrix[row_idx], candidates)
            rank = ordered.index(target_idx) + 1
            target_score = float(score_matrix[row_idx, target_idx])
            best_negative_idx = ordered[0] if ordered[0] != target_idx else (ordered[1] if len(ordered) > 1 else None)
            best_negative_score = float(score_matrix[row_idx, best_negative_idx]) if best_negative_idx is not None else 0.0
            margin = target_score - best_negative_score

            ranks.append(rank)
            margins.append(margin)
            negative_counts.append(len(negatives))
            for k in cfg.top_k:
                if rank <= min(k, len(candidates)):
                    hits[k] += 1

            ranking_rows.append(
                {
                    "dataset": dataset,
                    "model": model,
                    "strategy": strategy,
                    "sample_id": row["sample_id"],
                    "target_evidence_id": row["evidence_id"],
                    "rank": rank,
                    "n_negatives": len(negatives),
                    "target_score": target_score,
                    "best_negative_score": best_negative_score,
                    "positive_margin": margin,
                    "top_evidence_id": corpus.iloc[ordered[0]]["evidence_id"],
                    "top_is_negative": ordered[0] != target_idx,
                    "candidate_evidence_ids": json.dumps(
                        [str(corpus.iloc[idx]["evidence_id"]) for idx in ordered],
                        ensure_ascii=False,
                    ),
                }
            )

            if rank > 1 and len(failure_rows) < cfg.max_failure_examples:
                negative = corpus.iloc[ordered[0]]
                failure_rows.append(
                    {
                        "dataset": dataset,
                        "model": model,
                        "strategy": strategy,
                        "sample_id": row["sample_id"],
                        "rank": rank,
                        "question": row["question"],
                        "topic": row["topic"],
                        "skill": row["skill"],
                        "target_evidence": row["evidence_text"][:500],
                        "top_negative_sample_id": negative["sample_id"],
                        "top_negative_topic": negative["topic"],
                        "top_negative_skill": negative["skill"],
                        "top_negative_evidence": negative["evidence_text"][:500],
                    }
                )

        n = len(ranks)
        metric: dict[str, Any] = {
            "dataset": dataset,
            "model": model,
            "strategy": strategy,
            "n_queries": n,
            "n_skipped": skipped,
            "n_corpus": len(corpus),
            "avg_negatives": float(np.mean(negative_counts)) if negative_counts else 0.0,
            "mrr": float(np.mean([1.0 / rank for rank in ranks])) if ranks else 0.0,
            "hard_negative_top1_error_rate": float(np.mean([rank > 1 for rank in ranks])) if ranks else 0.0,
            "mean_positive_margin": float(np.mean(margins)) if margins else 0.0,
            "median_positive_margin": float(np.median(margins)) if margins else 0.0,
        }
        for k in cfg.top_k:
            metric[f"recall_at_{k}"] = hits[k] / n if n else 0.0
        metric_rows.append(metric)

    return metric_rows, failure_rows, pd.DataFrame(ranking_rows)


def lexical_similarity_matrix(texts: list[str], cfg: Config) -> np.ndarray:
    if not texts:
        return np.empty((0, 0))
    matrix, _ = fit_transform_tfidf(texts, texts, cfg)
    sims = matrix @ matrix.T
    np.fill_diagonal(sims, -1.0)
    return sims


def wrong_image_indices(
    strategy: str,
    row_idx: int,
    image_rows: pd.DataFrame,
    lexical_sims: np.ndarray,
    cfg: Config,
) -> list[int]:
    row = image_rows.iloc[row_idx]
    candidates = [idx for idx in range(len(image_rows)) if idx != row_idx]
    if strategy == "random_wrong_image":
        return stable_sample(
            candidates,
            cfg.wrong_image_max_negatives_per_query,
            f"{strategy}|{row['sample_id']}",
            cfg.random_seed,
        )
    if strategy == "lexical_wrong_image":
        ranked = sorted(candidates, key=lambda idx: (-float(lexical_sims[row_idx, idx]), idx))
        return ranked[: cfg.wrong_image_max_negatives_per_query]
    if strategy == "same_topic_wrong_image":
        topic = normalize_text(row.get("topic", ""))
        candidates = [idx for idx in candidates if normalize_text(image_rows.iloc[idx].get("topic", "")) == topic and topic]
    elif strategy == "same_skill_wrong_image":
        skill = normalize_text(row.get("skill", ""))
        candidates = [idx for idx in candidates if normalize_text(image_rows.iloc[idx].get("skill", "")) == skill and skill]
    else:
        raise ValueError(f"Unknown wrong-image strategy: {strategy}")
    ranked = sorted(candidates, key=lambda idx: (-float(lexical_sims[row_idx, idx]), idx))
    return ranked[: cfg.wrong_image_max_negatives_per_query]


def build_wrong_image_candidates(data: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    image_rows = data[
        (data["dataset"] == cfg.wrong_image_dataset)
        & (data["has_image"] == 1)
        & (data["image_ref"].str.len() > 0)
    ].copy()
    image_rows = image_rows.reset_index(drop=True)
    if image_rows.empty:
        return pd.DataFrame()

    texts = [
        " ".join(
            normalize_text(row.get(column, ""))
            for column in ["question", "choices", "answer", "topic", "skill"]
        )
        for _, row in image_rows.iterrows()
    ]
    lexical_sims = lexical_similarity_matrix(texts, cfg)
    rows: list[dict[str, Any]] = []
    for row_idx, row in image_rows.iterrows():
        for strategy in cfg.wrong_image_strategies:
            for negative_idx in wrong_image_indices(strategy, row_idx, image_rows, lexical_sims, cfg):
                negative = image_rows.iloc[negative_idx]
                rows.append(
                    {
                        "dataset": cfg.wrong_image_dataset,
                        "strategy": strategy,
                        "sample_id": row["sample_id"],
                        "question": row["question"],
                        "positive_image_ref": row["image_ref"],
                        "negative_sample_id": negative["sample_id"],
                        "negative_question": negative["question"],
                        "negative_image_ref": negative["image_ref"],
                        "lexical_similarity": float(lexical_sims[row_idx, negative_idx]),
                    }
                )
    return pd.DataFrame(rows)


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
    skipped: pd.DataFrame,
    failures: pd.DataFrame,
    wrong_image_candidates: pd.DataFrame,
) -> None:
    cfg.report_dir.mkdir(parents=True, exist_ok=True)
    metric_view = metrics.copy()
    for col in metric_view.columns:
        if metric_view[col].dtype.kind == "f":
            metric_view[col] = metric_view[col].map(format_float)

    best_rows = []
    if not metrics.empty:
        for dataset, frame in metrics.groupby("dataset"):
            for strategy, strat_frame in frame.groupby("strategy"):
                best = strat_frame.sort_values(["recall_at_1", "mrr"], ascending=False).iloc[0]
                best_rows.append(
                    {
                        "dataset": dataset,
                        "strategy": strategy,
                        "best_model": best["model"],
                        "n_queries": int(best["n_queries"]),
                        "recall_at_1": format_float(float(best["recall_at_1"])),
                        "mrr": format_float(float(best["mrr"])),
                        "top1_error": format_float(float(best["hard_negative_top1_error_rate"])),
                    }
                )

    coverage_rows = []
    for dataset, frame in data.groupby("dataset"):
        coverage_rows.append(
            {
                "dataset": dataset,
                "samples": len(frame),
                "text_evidence_queries": int((frame["evidence_text"].str.len() >= cfg.min_evidence_chars).sum()),
                "image_rows": int((frame["has_image"] == 1).sum()),
            }
        )

    wrong_image_summary = pd.DataFrame()
    if not wrong_image_candidates.empty:
        wrong_image_summary = (
            wrong_image_candidates.groupby("strategy")
            .agg(
                pairs=("negative_image_ref", "count"),
                queries=("sample_id", "nunique"),
                mean_lexical_similarity=("lexical_similarity", "mean"),
            )
            .reset_index()
        )
        wrong_image_summary["mean_lexical_similarity"] = wrong_image_summary[
            "mean_lexical_similarity"
        ].map(format_float)

    lines = [
        "# Exp1.2 Hard Negative 与 Wrong-image 候选构造",
        "",
        "## 目标",
        "",
        "在 Exp1.1 文本证据检索 baseline 之上，加入同 subject、同 topic、同 skill 等 hard negative 候选池，检查模型是否真的对齐了解题证据，而不是只依赖宽泛语义相似。",
        "",
        "同时为 AI2D 生成 wrong-image 候选表，作为后续 CLIP / SigLIP 图像证据检索和 RC2 wrong-image 鲁棒性实验输入。",
        "",
        "## 数据覆盖",
        "",
        df_to_markdown(pd.DataFrame(coverage_rows)),
        "",
        "## Hard Negative 最优结果",
        "",
        df_to_markdown(pd.DataFrame(best_rows)),
        "",
        "## 全部 Hard Negative 指标",
        "",
        df_to_markdown(metric_view),
        "",
    ]
    if not skipped.empty:
        lines.extend(["## 跳过情况", "", df_to_markdown(skipped), ""])
    if not wrong_image_summary.empty:
        lines.extend(
            [
                "## AI2D Wrong-image 候选",
                "",
                df_to_markdown(wrong_image_summary),
                "",
                f"候选明细已写入 `{cfg.report_dir / 'wrong_image_candidates.csv'}`。",
                "",
            ]
        )
    if not failures.empty:
        lines.extend(
            [
                "## 失败样例",
                "",
                "以下样例展示 hard-negative 候选池中排在正确证据前面的负样本。",
                "",
                df_to_markdown(failures.head(cfg.max_failure_examples)),
                "",
            ]
        )
    lines.extend(
        [
            "## 结果解读",
            "",
            "- ScienceQA 的同 topic / 同 skill hard negative 更接近真实论文问题，因为它们会把相似教学目标下的不同证据放进同一候选池。",
            "- TQA / CK12 当前公开 instruction 样例的文本证据高度重复，hard negative 指标容易被粗粒度 lesson 文本限制，后续仍需官方完整教材段落。",
            "- AI2D 当前 schema 只有 `hf://` 图像引用，没有本地图像像素；本实验先输出 wrong-image 候选，不声称已经完成 CLIP / SigLIP 图像检索。",
            "",
            "## 下一步",
            "",
            "1. 下载或缓存 AI2D / TQA 原始图像，补齐本地图像证据文件。",
            "2. 在 wrong-image 候选表上运行 CLIP / SigLIP 图文检索 baseline。",
            "3. 将 hard negative 候选池复用到后续 Sentence-BERT 文本检索 baseline。",
            "",
        ]
    )
    (cfg.report_dir / "run_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/exp1_2_hard_negative_retrieval.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    cfg.report_dir.mkdir(parents=True, exist_ok=True)

    data = load_samples(cfg.input_samples, cfg)
    metric_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    ranking_frames: list[pd.DataFrame] = []
    skipped_rows: list[dict[str, Any]] = []

    for dataset in sorted(data["dataset"].unique()):
        eval_rows, corpus = prepare_text_dataset(data, dataset, cfg)
        if eval_rows.empty or len(corpus) < 2:
            skipped_rows.append(
                {
                    "dataset": dataset,
                    "reason": "文本证据为空或候选证据少于 2 条",
                    "n_queries": len(eval_rows),
                    "n_corpus": len(corpus),
                }
            )
            continue

        model_scores = {
            "tfidf": score_tfidf(eval_rows, corpus, cfg),
            "bm25": score_bm25(eval_rows, corpus, cfg),
        }
        for model, scores in model_scores.items():
            metrics, failures, rankings = evaluate_hard_negatives(dataset, model, eval_rows, corpus, scores, cfg)
            metric_rows.extend(metrics)
            failure_rows.extend(failures)
            ranking_frames.append(rankings)

    metrics = pd.DataFrame(metric_rows)
    failures = pd.DataFrame(failure_rows)
    rankings = pd.concat(ranking_frames, ignore_index=True, sort=False) if ranking_frames else pd.DataFrame()
    skipped = pd.DataFrame(skipped_rows)
    wrong_image_candidates = build_wrong_image_candidates(data, cfg)

    metrics.to_csv(cfg.report_dir / "metrics.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    failures.to_csv(cfg.report_dir / "failure_examples.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    rankings.to_csv(cfg.report_dir / "hard_negative_rankings.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    skipped.to_csv(cfg.report_dir / "skipped_datasets.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    wrong_image_candidates.to_csv(
        cfg.report_dir / "wrong_image_candidates.csv",
        index=False,
        quoting=csv.QUOTE_MINIMAL,
    )
    write_summary(cfg, data, metrics, skipped, failures, wrong_image_candidates)
    print(f"Wrote {cfg.report_dir}")


if __name__ == "__main__":
    main()
