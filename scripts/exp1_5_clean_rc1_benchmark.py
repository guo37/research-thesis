"""Exp1.5 构造干净 RC1 benchmark。

本实验把 Exp1.4 的审计结论落成后续 scorer 可直接使用的数据表：

- 文本证据使用 no-solution evidence，降低答案泄漏；
- hard negative 使用固定负样本数和共同 query 子集；
- 文本 split 按 positive evidence_id 划分，避免同一证据跨 split；
- AI2D 图像候选按 diagram hash 去重，过滤 same-diagram wrong image；
- AI2D split 按 diagram hash 划分，避免同一 diagram 跨 split。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
from collections import Counter
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


TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
LABEL_RE = re.compile(r"(?is)(hint|lecture|solution|lesson):")


DEFAULT_CONFIG: dict[str, Any] = {
    "paths": {
        "report_dir": "reports/exp1_5_clean_rc1_benchmark",
        "input_samples": [
            "data/educational_mm/schema_samples/scienceqa_schema_sample.csv",
            "data/educational_mm/schema_samples/tqa_ck12_schema_sample.csv",
            "data/educational_mm/schema_samples/ai2d_schema_sample.csv",
        ],
        "ai2d_image_manifest": "reports/exp1_3_visual_evidence_retrieval/ai2d_image_manifest.csv",
        "ai2d_wrong_image_eval": "reports/exp1_3_visual_evidence_retrieval/wrong_image_eval.csv",
    },
    "split": {"train": 0.70, "dev": 0.15, "test": 0.15, "random_seed": 42},
    "text_benchmark": {
        "datasets": ["scienceqa", "tqa_ck12"],
        "query_variant": "question_choices_topic_skill",
        "evidence_variant": "no_solution",
        "min_evidence_chars": 5,
        "fixed_negatives_per_strategy": 1,
        "strategies": ["random", "same_subject", "same_topic", "same_skill"],
        "top_k": [1, 5, 10],
    },
    "visual_benchmark": {
        "dataset": "ai2d",
        "fixed_negatives_per_strategy": 1,
        "strategies": [
            "random_wrong_image",
            "lexical_wrong_image",
            "same_topic_wrong_image",
            "same_skill_wrong_image",
        ],
        "top_k": [1, 5, 10],
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
    ai2d_image_manifest: Path
    ai2d_wrong_image_eval: Path
    split_train: float
    split_dev: float
    split_test: float
    random_seed: int
    text_datasets: list[str]
    text_query_variant: str
    text_evidence_variant: str
    text_min_evidence_chars: int
    text_fixed_negatives: int
    text_strategies: list[str]
    text_top_k: list[int]
    visual_dataset: str
    visual_fixed_negatives: int
    visual_strategies: list[str]
    visual_top_k: list[int]
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
    if path and yaml is not None:
        with open(path, "r", encoding="utf-8") as f:
            raw = deep_update(DEFAULT_CONFIG, yaml.safe_load(f) or {})
    elif path and yaml is None:
        print("PyYAML is not installed; using built-in Exp1.5 config.")

    split = raw["split"]
    text = raw["text_benchmark"]
    visual = raw["visual_benchmark"]
    tfidf = raw["models"]["tfidf"]
    bm25 = raw["models"]["bm25"]
    ngram_range = tuple(int(x) for x in tfidf["ngram_range"])
    return Config(
        report_dir=Path(raw["paths"]["report_dir"]),
        input_samples=[Path(p) for p in raw["paths"]["input_samples"]],
        ai2d_image_manifest=Path(raw["paths"]["ai2d_image_manifest"]),
        ai2d_wrong_image_eval=Path(raw["paths"]["ai2d_wrong_image_eval"]),
        split_train=float(split["train"]),
        split_dev=float(split["dev"]),
        split_test=float(split["test"]),
        random_seed=int(split["random_seed"]),
        text_datasets=list(text["datasets"]),
        text_query_variant=str(text["query_variant"]),
        text_evidence_variant=str(text["evidence_variant"]),
        text_min_evidence_chars=int(text["min_evidence_chars"]),
        text_fixed_negatives=int(text["fixed_negatives_per_strategy"]),
        text_strategies=list(text["strategies"]),
        text_top_k=sorted(int(k) for k in text["top_k"]),
        visual_dataset=str(visual["dataset"]),
        visual_fixed_negatives=int(visual["fixed_negatives_per_strategy"]),
        visual_strategies=list(visual["strategies"]),
        visual_top_k=sorted(int(k) for k in visual["top_k"]),
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


def stable_id(*parts: Any, length: int = 16) -> str:
    text = "|".join(normalize_text(part) for part in parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:length]


def split_for_group(group_id: str, cfg: Config) -> str:
    score = int(stable_id(cfg.random_seed, "split", group_id, length=12), 16) / float(16**12 - 1)
    train_cut = cfg.split_train
    dev_cut = cfg.split_train + cfg.split_dev
    if score < train_cut:
        return "train"
    if score < dev_cut:
        return "dev"
    return "test"


def balanced_split_map(group_ids: list[str], cfg: Config) -> dict[str, str]:
    unique_ids = sorted(set(group_ids), key=lambda group_id: stable_id(cfg.random_seed, "split-order", group_id, length=24))
    n_groups = len(unique_ids)
    if n_groups == 0:
        return {}
    n_train = int(round(n_groups * cfg.split_train))
    n_dev = int(round(n_groups * cfg.split_dev))
    n_train = max(1, min(n_train, n_groups)) if n_groups >= 3 else max(0, min(n_train, n_groups))
    remaining = n_groups - n_train
    n_dev = max(1, min(n_dev, remaining)) if remaining >= 2 else max(0, min(n_dev, remaining))
    n_test = n_groups - n_train - n_dev
    if n_groups >= 3 and n_test == 0:
        if n_train >= n_dev and n_train > 1:
            n_train -= 1
        elif n_dev > 1:
            n_dev -= 1
        n_test = n_groups - n_train - n_dev
    out: dict[str, str] = {}
    for idx, group_id in enumerate(unique_ids):
        if idx < n_train:
            out[group_id] = "train"
        elif idx < n_train + n_dev:
            out[group_id] = "dev"
        else:
            out[group_id] = "test"
    return out


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def text_terms(text: str, ngram_range: tuple[int, int]) -> list[str]:
    tokens = tokenize(text)
    terms: list[str] = []
    min_n, max_n = ngram_range
    for n in range(min_n, max_n + 1):
        if len(tokens) < n:
            continue
        terms.extend(" ".join(tokens[idx : idx + n]) for idx in range(len(tokens) - n + 1))
    return terms


def parse_labeled_segments(text: str) -> dict[str, str]:
    text = "" if pd.isna(text) else str(text)
    matches = list(LABEL_RE.finditer(text))
    if not matches:
        return {"unlabeled": text.strip()} if text.strip() else {}
    segments: dict[str, list[str]] = {}
    for idx, match in enumerate(matches):
        label = match.group(1).lower()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        value = text[start:end].strip()
        if value:
            segments.setdefault(label, []).append(value)
    return {label: "\n".join(values) for label, values in segments.items()}


def evidence_variant_text(text: str, variant: str) -> str:
    text = normalize_text(text)
    segments = parse_labeled_segments(text)
    if variant == "full":
        return text
    if variant == "no_solution":
        if not segments:
            return text
        return normalize_text("\n".join(value for label, value in segments.items() if label != "solution"))
    if variant == "hint_lecture":
        return normalize_text("\n".join(value for label, value in segments.items() if label in {"hint", "lecture"}))
    raise ValueError(f"Unknown evidence variant: {variant}")


def make_query(row: pd.Series, variant: str) -> str:
    columns_by_variant = {
        "question_only": ["question"],
        "question_choices": ["question", "choices"],
        "question_choices_topic_skill": ["question", "choices", "topic", "skill"],
    }
    columns = columns_by_variant.get(variant)
    if columns is None:
        raise ValueError(f"Unknown query variant: {variant}")
    return " ".join(normalize_text(row.get(column, "")) for column in columns if normalize_text(row.get(column, "")))


def load_samples(paths: list[Path]) -> pd.DataFrame:
    frames = []
    for path in paths:
        data = pd.read_csv(path)
        data["source_file"] = str(path)
        frames.append(data)
    data = pd.concat(frames, ignore_index=True, sort=False)
    for column in [
        "dataset",
        "sample_id",
        "subject",
        "topic",
        "skill",
        "question",
        "choices",
        "answer",
        "text_context",
        "image_ref",
    ]:
        if column in data.columns:
            data[column] = data[column].fillna("").astype(str)
    return data


def build_tfidf_vocab(texts: list[str], cfg: Config) -> tuple[dict[str, int], Counter[str]]:
    doc_freq: Counter[str] = Counter()
    for text in texts:
        doc_freq.update(set(text_terms(text, cfg.tfidf_ngram_range)))
    terms = [term for term, freq in doc_freq.items() if freq >= cfg.tfidf_min_df]
    terms = sorted(terms, key=lambda term: (-doc_freq[term], term))
    if cfg.tfidf_max_features > 0:
        terms = terms[: cfg.tfidf_max_features]
    return {term: idx for idx, term in enumerate(terms)}, doc_freq


def transform_tfidf(texts: list[str], vocab: dict[str, int], doc_freq: Counter[str], n_docs: int, cfg: Config) -> np.ndarray:
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


def pairwise_tfidf_scores(pairs: pd.DataFrame, cfg: Config) -> pd.Series:
    if pairs.empty:
        return pd.Series(dtype=float)
    texts = pd.concat([pairs["query_text"], pairs["candidate_text"]], ignore_index=True).fillna("").astype(str).tolist()
    vocab, doc_freq = build_tfidf_vocab(texts, cfg)
    query_matrix = transform_tfidf(pairs["query_text"].tolist(), vocab, doc_freq, len(texts), cfg)
    candidate_matrix = transform_tfidf(pairs["candidate_text"].tolist(), vocab, doc_freq, len(texts), cfg)
    return pd.Series(np.sum(query_matrix * candidate_matrix, axis=1), index=pairs.index)


def bm25_pair_score(query: str, document: str, corpus_df: Counter[str], n_docs: int, avgdl: float, cfg: Config) -> float:
    query_terms = tokenize(query)
    doc_terms = tokenize(document)
    if not query_terms or not doc_terms:
        return 0.0
    doc_counts = Counter(doc_terms)
    score = 0.0
    dl = len(doc_terms)
    for term, qf in Counter(query_terms).items():
        tf = doc_counts.get(term, 0)
        if tf == 0:
            continue
        df = corpus_df.get(term, 0)
        idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
        denom = tf + cfg.bm25_k1 * (1 - cfg.bm25_b + cfg.bm25_b * dl / avgdl) if avgdl else tf + cfg.bm25_k1
        score += idf * (tf * (cfg.bm25_k1 + 1) / denom) * qf
    return float(score)


def pairwise_bm25_scores(pairs: pd.DataFrame, cfg: Config) -> pd.Series:
    if pairs.empty:
        return pd.Series(dtype=float)
    docs = pairs["candidate_text"].fillna("").astype(str).tolist()
    tokenized_docs = [tokenize(doc) for doc in docs]
    corpus_df: Counter[str] = Counter()
    for doc in tokenized_docs:
        corpus_df.update(set(doc))
    avgdl = float(np.mean([len(doc) for doc in tokenized_docs])) if tokenized_docs else 0.0
    n_docs = len(tokenized_docs)
    scores = [
        bm25_pair_score(query, doc, corpus_df, n_docs, avgdl, cfg)
        for query, doc in zip(pairs["query_text"].tolist(), docs)
    ]
    return pd.Series(scores, index=pairs.index)


def stable_sample(indices: list[int], limit: int, key: str, seed: int) -> list[int]:
    if len(indices) <= limit:
        return sorted(indices)
    ranked = sorted(indices, key=lambda idx: stable_id(seed, key, idx, length=24))
    return sorted(ranked[:limit])


def negative_indices(strategy: str, row: pd.Series, corpus: pd.DataFrame, target_idx: int, required_split: str | None = None) -> list[int]:
    mask = corpus.index.to_series() != target_idx
    if required_split is not None and "split" in corpus.columns:
        mask &= corpus["split"] == required_split
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
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    return [int(idx) for idx in corpus.index[mask]]


def prepare_text_dataset(data: pd.DataFrame, dataset: str, cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    subset = data[data["dataset"] == dataset].copy()
    subset["query_text"] = subset.apply(lambda row: make_query(row, cfg.text_query_variant), axis=1)
    subset["evidence_text"] = subset["text_context"].map(lambda text: evidence_variant_text(text, cfg.text_evidence_variant))
    eval_rows = subset[
        (subset["query_text"].str.len() > 0) & (subset["evidence_text"].str.len() >= cfg.text_min_evidence_chars)
    ].copy()
    eval_rows["positive_evidence_id"] = eval_rows["evidence_text"].map(lambda text: stable_id("evidence", text))
    corpus = (
        eval_rows[
            [
                "positive_evidence_id",
                "evidence_text",
                "dataset",
                "subject",
                "topic",
                "skill",
                "sample_id",
            ]
        ]
        .drop_duplicates("positive_evidence_id")
        .rename(columns={"positive_evidence_id": "candidate_evidence_id", "evidence_text": "candidate_text"})
        .reset_index(drop=True)
    )
    return eval_rows.reset_index(drop=True), corpus


def build_text_pairs(data: pd.DataFrame, cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    pair_rows: list[dict[str, Any]] = []
    stats_rows: list[dict[str, Any]] = []
    for dataset in cfg.text_datasets:
        eval_rows, corpus = prepare_text_dataset(data, dataset, cfg)
        split_by_evidence = balanced_split_map(corpus["candidate_evidence_id"].astype(str).tolist(), cfg)
        corpus["split"] = corpus["candidate_evidence_id"].map(lambda value: split_by_evidence.get(value, "train"))
        evidence_to_idx = {evidence_id: idx for idx, evidence_id in enumerate(corpus["candidate_evidence_id"])}
        eligible_query_ids: set[str] = set()
        eligible_pools = 0
        for _, row in eval_rows.iterrows():
            target_idx = evidence_to_idx.get(row["positive_evidence_id"])
            if target_idx is None:
                continue
            target = corpus.iloc[target_idx]
            split = split_by_evidence.get(row["positive_evidence_id"], "train")
            for strategy in cfg.text_strategies:
                negatives = negative_indices(strategy, row, corpus, target_idx, split)
                if len(negatives) < cfg.text_fixed_negatives:
                    continue
                eligible_query_ids.add(str(row["sample_id"]))
                eligible_pools += 1
                pool_id = stable_id("text_pool", dataset, row["sample_id"], strategy)
                shared = {
                    "dataset": dataset,
                    "modality": "text",
                    "split": split,
                    "pool_id": pool_id,
                    "query_sample_id": row["sample_id"],
                    "query_text": row["query_text"],
                    "query_variant": cfg.text_query_variant,
                    "positive_evidence_id": row["positive_evidence_id"],
                    "evidence_variant": cfg.text_evidence_variant,
                    "negative_strategy": strategy,
                    "subject": row.get("subject", ""),
                    "topic": row.get("topic", ""),
                    "skill": row.get("skill", ""),
                }
                pair_rows.append(
                    {
                        **shared,
                        "pair_id": stable_id("text_pair", pool_id, target["candidate_evidence_id"], 1),
                        "candidate_sample_id": target["sample_id"],
                        "candidate_evidence_id": target["candidate_evidence_id"],
                        "candidate_text": target["candidate_text"],
                        "label": 1,
                    }
                )
                sampled = stable_sample(
                    negatives,
                    cfg.text_fixed_negatives,
                    f"{dataset}|{row['sample_id']}|{strategy}",
                    cfg.random_seed,
                )
                for neg_idx in sampled:
                    candidate = corpus.iloc[neg_idx]
                    pair_rows.append(
                        {
                            **shared,
                            "pair_id": stable_id("text_pair", pool_id, candidate["candidate_evidence_id"], 0),
                            "candidate_sample_id": candidate["sample_id"],
                            "candidate_evidence_id": candidate["candidate_evidence_id"],
                            "candidate_text": candidate["candidate_text"],
                            "label": 0,
                        }
                    )
        stats_rows.append(
            {
                "dataset": dataset,
                "raw_rows": len(data[data["dataset"] == dataset]),
                "eval_rows": len(eval_rows),
                "eligible_queries": len(eligible_query_ids),
                "eligible_pools": eligible_pools,
                "unique_evidence": len(corpus),
                "evidence_variant": cfg.text_evidence_variant,
                "query_variant": cfg.text_query_variant,
                "fixed_negatives_per_strategy": cfg.text_fixed_negatives,
                "strategies": "|".join(cfg.text_strategies),
            }
        )
    pairs = pd.DataFrame(pair_rows)
    if not pairs.empty:
        pairs["tfidf_score"] = pairwise_tfidf_scores(pairs, cfg)
        pairs["bm25_score"] = pairwise_bm25_scores(pairs, cfg)
    return pairs, pd.DataFrame(stats_rows)


def rank_pool(pool: pd.DataFrame, score_col: str) -> int | None:
    ranked = pool.sort_values([score_col, "label", "pair_id"], ascending=[False, False, True]).reset_index(drop=True)
    positives = ranked.index[ranked["label"] == 1].tolist()
    return positives[0] + 1 if positives else None


def evaluate_pools(pairs: pd.DataFrame, score_col: str, group_columns: list[str], top_k: list[int]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if pairs.empty:
        return pd.DataFrame(rows)
    for group_key, group in pairs.groupby(group_columns, dropna=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        hits = {k: 0 for k in top_k}
        rr_sum = 0.0
        n_pools = 0
        ranks = []
        for _, pool in group.groupby("pool_id"):
            rank = rank_pool(pool, score_col)
            if rank is None:
                continue
            n_pools += 1
            ranks.append(rank)
            rr_sum += 1.0 / rank
            for k in top_k:
                if rank <= k:
                    hits[k] += 1
        out = dict(zip(group_columns, group_key))
        out.update(
            {
                "model": score_col.replace("_score", ""),
                "n_queries": n_pools,
                "candidate_pool_size_mean": float(group.groupby("pool_id").size().mean()) if n_pools else 0.0,
                "mrr": rr_sum / n_pools if n_pools else 0.0,
                "mean_rank": float(np.mean(ranks)) if ranks else 0.0,
                "top1_error_rate": 1.0 - (hits[1] / n_pools) if n_pools and 1 in hits else 0.0,
            }
        )
        for k in top_k:
            out[f"recall_at_{k}"] = hits[k] / n_pools if n_pools else 0.0
        rows.append(out)
    return pd.DataFrame(rows)


def make_combined_pairs(pairs: pd.DataFrame) -> pd.DataFrame:
    if pairs.empty:
        return pairs.copy()
    rows = []
    for (_, _, sample_id), group in pairs.groupby(["dataset", "split", "query_sample_id"], dropna=False):
        first = group.iloc[0]
        positives = group[group["label"] == 1].drop_duplicates("candidate_evidence_id")
        negatives = group[group["label"] == 0].drop_duplicates("candidate_evidence_id")
        pool_id = stable_id("combined_text_pool", first["dataset"], first["query_sample_id"])
        combined = pd.concat([positives, negatives], ignore_index=True)
        combined["pool_id"] = pool_id
        combined["negative_strategy"] = "combined"
        rows.append(combined)
    return pd.concat(rows, ignore_index=True) if rows else pairs.iloc[0:0].copy()


def evaluate_text_pairs(pairs: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    if pairs.empty:
        return pd.DataFrame()
    combined = make_combined_pairs(pairs)
    eval_pairs = pd.concat([pairs, combined], ignore_index=True)
    metric_frames = []
    for score_col in ["tfidf_score", "bm25_score"]:
        metric_frames.append(
            evaluate_pools(
                eval_pairs,
                score_col,
                ["dataset", "modality", "split", "negative_strategy"],
                cfg.text_top_k,
            )
        )
    return pd.concat(metric_frames, ignore_index=True) if metric_frames else pd.DataFrame()


def image_hash(path: str) -> str:
    with Image.open(path) as image:
        return hashlib.sha1(image.convert("RGB").tobytes()).hexdigest()


def load_ai2d_manifest(cfg: Config) -> pd.DataFrame:
    manifest = pd.read_csv(cfg.ai2d_image_manifest)
    manifest = manifest[manifest["status"] == "cached"].copy()
    manifest["local_image_path"] = manifest["local_image_path"].map(normalize_text)
    manifest["diagram_hash"] = manifest["local_image_path"].map(image_hash)
    manifest["diagram_group_size"] = manifest.groupby("diagram_hash")["diagram_hash"].transform("size")
    split_by_diagram = balanced_split_map(manifest["diagram_hash"].astype(str).tolist(), cfg)
    manifest["split"] = manifest["diagram_hash"].map(lambda value: split_by_diagram.get(value, "train"))
    return manifest


def build_visual_pairs(data: pd.DataFrame, manifest: pd.DataFrame, cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not cfg.ai2d_wrong_image_eval.exists() or manifest.empty:
        return pd.DataFrame(), pd.DataFrame()

    ai2d = data[data["dataset"] == cfg.visual_dataset].copy()
    ai2d["query_text"] = ai2d.apply(lambda row: make_query(row, "question_choices_topic_skill"), axis=1)
    sample_to_query = dict(zip(ai2d["sample_id"], ai2d["query_text"]))
    sample_to_ref = dict(zip(manifest["sample_id"], manifest["image_ref"]))
    sample_to_path = dict(zip(manifest["sample_id"], manifest["local_image_path"]))
    sample_to_hash = dict(zip(manifest["sample_id"], manifest["diagram_hash"]))
    sample_to_split = dict(zip(manifest["sample_id"], manifest["split"]))
    sample_to_group_size = dict(zip(manifest["sample_id"], manifest["diagram_group_size"]))

    wrong = pd.read_csv(cfg.ai2d_wrong_image_eval)
    wrong = wrong[wrong["strategy"].isin(cfg.visual_strategies)].copy()
    wrong["positive_diagram_hash"] = wrong["sample_id"].map(sample_to_hash)
    wrong["candidate_diagram_hash"] = wrong["negative_sample_id"].map(sample_to_hash)
    wrong = wrong[
        wrong["positive_diagram_hash"].notna()
        & wrong["candidate_diagram_hash"].notna()
        & (wrong["positive_diagram_hash"] != wrong["candidate_diagram_hash"])
    ].copy()
    base_candidates = wrong[["strategy", "sample_id", "negative_sample_id"]].drop_duplicates()
    base_candidates["positive_split"] = base_candidates["sample_id"].map(sample_to_split)
    base_candidates["negative_split"] = base_candidates["negative_sample_id"].map(sample_to_split)
    base_candidates = base_candidates[
        base_candidates["positive_split"].notna()
        & base_candidates["negative_split"].notna()
        & (base_candidates["positive_split"] == base_candidates["negative_split"])
    ].copy()

    pair_rows: list[dict[str, Any]] = []
    stats_rows = [
        {
            "dataset": cfg.visual_dataset,
            "cached_images": len(manifest),
            "unique_diagram_hashes": int(manifest["diagram_hash"].nunique()),
            "duplicate_groups": int((manifest["diagram_hash"].value_counts() > 1).sum()),
            "images_in_duplicate_groups": int(manifest["diagram_group_size"].gt(1).sum()),
            "fixed_negatives_per_strategy": cfg.visual_fixed_negatives,
            "strategies": "|".join(cfg.visual_strategies),
        }
    ]
    for sample_id, group in base_candidates.groupby("sample_id"):
        if sample_id not in sample_to_hash:
            continue
        for strategy in cfg.visual_strategies:
            candidates = group[group["strategy"] == strategy]["negative_sample_id"].dropna().astype(str).tolist()
            if len(candidates) < cfg.visual_fixed_negatives:
                continue
            sampled = stable_sample(
                list(range(len(candidates))),
                cfg.visual_fixed_negatives,
                f"{cfg.visual_dataset}|{sample_id}|{strategy}",
                cfg.random_seed,
            )
            pool_id = stable_id("visual_pool", cfg.visual_dataset, sample_id, strategy)
            shared = {
                "dataset": cfg.visual_dataset,
                "modality": "image",
                "split": sample_to_split.get(sample_id, ""),
                "pool_id": pool_id,
                "query_sample_id": sample_id,
                "query_text": sample_to_query.get(sample_id, ""),
                "query_variant": "question_choices_topic_skill",
                "positive_diagram_hash": sample_to_hash.get(sample_id, ""),
                "negative_strategy": strategy,
            }
            pair_rows.append(
                {
                    **shared,
                    "pair_id": stable_id("visual_pair", pool_id, sample_id, 1),
                    "candidate_sample_id": sample_id,
                    "candidate_image_ref": sample_to_ref.get(sample_id, ""),
                    "candidate_local_image_path": sample_to_path.get(sample_id, ""),
                    "candidate_diagram_hash": sample_to_hash.get(sample_id, ""),
                    "candidate_diagram_group_size": sample_to_group_size.get(sample_id, 0),
                    "label": 1,
                }
            )
            for idx in sampled:
                negative_sample_id = candidates[idx]
                pair_rows.append(
                    {
                        **shared,
                        "pair_id": stable_id("visual_pair", pool_id, negative_sample_id, 0),
                        "candidate_sample_id": negative_sample_id,
                        "candidate_image_ref": sample_to_ref.get(negative_sample_id, ""),
                        "candidate_local_image_path": sample_to_path.get(negative_sample_id, ""),
                        "candidate_diagram_hash": sample_to_hash.get(negative_sample_id, ""),
                        "candidate_diagram_group_size": sample_to_group_size.get(negative_sample_id, 0),
                        "label": 0,
                    }
                )
    pairs = pd.DataFrame(pair_rows)
    return pairs, pd.DataFrame(stats_rows)


def evaluate_visual_pairs(visual_pairs: pd.DataFrame, manifest: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    if visual_pairs.empty or not cfg.ai2d_wrong_image_eval.exists():
        return pd.DataFrame()
    selected_negatives = visual_pairs[visual_pairs["label"] == 0][
        ["negative_strategy", "query_sample_id", "candidate_sample_id", "split", "pool_id"]
    ].rename(
        columns={
            "negative_strategy": "strategy",
            "query_sample_id": "sample_id",
            "candidate_sample_id": "negative_sample_id",
        }
    )
    wrong = pd.read_csv(cfg.ai2d_wrong_image_eval)
    wrong = wrong.merge(selected_negatives, on=["strategy", "sample_id", "negative_sample_id"], how="inner")
    hash_by_sample = dict(zip(manifest["sample_id"], manifest["diagram_hash"]))
    wrong["positive_diagram_hash"] = wrong["sample_id"].map(hash_by_sample)
    wrong["negative_diagram_hash"] = wrong["negative_sample_id"].map(hash_by_sample)
    wrong = wrong[wrong["positive_diagram_hash"] != wrong["negative_diagram_hash"]].copy()
    if wrong.empty:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for (model, split, strategy), group in wrong.groupby(["model", "split", "strategy"]):
        pool_rows = []
        for pool_id, pool in group.groupby("pool_id"):
            pos_score = float(pool["positive_score"].iloc[0])
            candidates = [(pool["sample_id"].iloc[0], 1, pos_score)]
            for _, row in pool.iterrows():
                candidates.append((row["negative_sample_id"], 0, float(row["negative_score"])))
            ranked = sorted(candidates, key=lambda item: (-item[2], -item[1], item[0]))
            rank = next(idx + 1 for idx, item in enumerate(ranked) if item[1] == 1)
            pool_rows.append({"pool_id": pool_id, "rank": rank, "pool_size": len(candidates)})
        n = len(pool_rows)
        ranks = [row["rank"] for row in pool_rows]
        out = {
            "dataset": cfg.visual_dataset,
            "modality": "image",
            "split": split,
            "negative_strategy": strategy,
            "model": model,
            "n_queries": n,
            "candidate_pool_size_mean": float(np.mean([row["pool_size"] for row in pool_rows])) if pool_rows else 0.0,
            "mrr": float(np.mean([1.0 / rank for rank in ranks])) if ranks else 0.0,
            "mean_rank": float(np.mean(ranks)) if ranks else 0.0,
            "top1_error_rate": float(np.mean([rank > 1 for rank in ranks])) if ranks else 0.0,
        }
        for k in cfg.visual_top_k:
            out[f"recall_at_{k}"] = float(np.mean([rank <= k for rank in ranks])) if ranks else 0.0
        rows.append(out)

    combined_rows: list[dict[str, Any]] = []
    for (model, split), group in wrong.groupby(["model", "split"]):
        pool_rows = []
        for sample_id, pool in group.groupby("sample_id"):
            pos_score = float(pool["positive_score"].iloc[0])
            candidates = [(sample_id, 1, pos_score)]
            for _, row in pool.drop_duplicates("negative_sample_id").iterrows():
                candidates.append((row["negative_sample_id"], 0, float(row["negative_score"])))
            ranked = sorted(candidates, key=lambda item: (-item[2], -item[1], item[0]))
            rank = next(idx + 1 for idx, item in enumerate(ranked) if item[1] == 1)
            pool_rows.append({"rank": rank, "pool_size": len(candidates)})
        n = len(pool_rows)
        ranks = [row["rank"] for row in pool_rows]
        out = {
            "dataset": cfg.visual_dataset,
            "modality": "image",
            "split": split,
            "negative_strategy": "combined",
            "model": model,
            "n_queries": n,
            "candidate_pool_size_mean": float(np.mean([row["pool_size"] for row in pool_rows])) if pool_rows else 0.0,
            "mrr": float(np.mean([1.0 / rank for rank in ranks])) if ranks else 0.0,
            "mean_rank": float(np.mean(ranks)) if ranks else 0.0,
            "top1_error_rate": float(np.mean([rank > 1 for rank in ranks])) if ranks else 0.0,
        }
        for k in cfg.visual_top_k:
            out[f"recall_at_{k}"] = float(np.mean([rank <= k for rank in ranks])) if ranks else 0.0
        combined_rows.append(out)
    return pd.DataFrame(rows + combined_rows)


def df_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_无记录。_"
    view = df.fillna("").copy()
    for col in view.columns:
        if view[col].dtype.kind == "f":
            view[col] = view[col].map(lambda value: f"{value:.4f}")
    view = view.astype(str)
    headers = list(view.columns)
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for _, row in view.iterrows():
        safe = [str(row[col]).replace("\n", "<br>").replace("|", "\\|") for col in headers]
        lines.append("| " + " | ".join(safe) + " |")
    return "\n".join(lines)


def write_run_record(cfg: Config) -> None:
    lines = [
        "# 实验运行记录",
        "",
        "## 元数据",
        "",
        "- 日期：2026-07-01",
        "- 实验：Exp1.5 clean RC1 benchmark",
        "- 分支：main",
        "- 提交：运行后填写",
        "- 设备：Windows",
        "- 环境：my_research",
        "",
        "## 研究问题",
        "",
        "把 RC1 的文本和图像证据检索评测切换为无泄漏、固定负样本数、diagram-level 去重的干净 benchmark。",
        "",
        "## 配置",
        "",
        "- 配置文件：configs/exp1_5_clean_rc1_benchmark.yaml",
        "- 数据集：ScienceQA、TQA / CK12、AI2D schema samples",
        "- 输入路径：data/educational_mm/schema_samples，reports/exp1_3_visual_evidence_retrieval",
        f"- 输出路径：{cfg.report_dir.as_posix()}",
        "",
        "## 命令",
        "",
        "```powershell",
        "conda run -n my_research python scripts/exp1_5_clean_rc1_benchmark.py --config configs/exp1_5_clean_rc1_benchmark.yaml",
        "```",
        "",
        "## 结果",
        "",
        "- 主要指标：见 run_summary.md、text_pair_metrics.csv、visual_pair_metrics.csv。",
        "- 基线：TF-IDF / BM25 文本打分，CLIP / SigLIP wrong-image 分数复用 Exp1.3。",
        "- 对比：no-solution 文本证据、固定 hard negative、nonduplicate wrong image。",
        "",
        "## 解读",
        "",
        "见 run_summary.md。",
        "",
        "## 下一步",
        "",
        "基于 rc1_text_benchmark_pairs.csv 训练 evidence alignment scorer。",
        "",
    ]
    (cfg.report_dir / "run_record_2026-07-01.md").write_text("\n".join(lines), encoding="utf-8")


def write_summary(
    cfg: Config,
    text_pairs: pd.DataFrame,
    text_stats: pd.DataFrame,
    text_metrics: pd.DataFrame,
    visual_pairs: pd.DataFrame,
    visual_stats: pd.DataFrame,
    visual_metrics: pd.DataFrame,
    diagram_groups: pd.DataFrame,
) -> None:
    text_test = text_metrics[text_metrics["split"] == "test"].copy() if not text_metrics.empty else pd.DataFrame()
    visual_test = visual_metrics[visual_metrics["split"] == "test"].copy() if not visual_metrics.empty else pd.DataFrame()
    text_pair_counts = (
        text_pairs.groupby(["dataset", "split", "label"]).size().reset_index(name="pairs")
        if not text_pairs.empty
        else pd.DataFrame()
    )
    visual_pair_counts = (
        visual_pairs.groupby(["dataset", "split", "label"]).size().reset_index(name="pairs")
        if not visual_pairs.empty
        else pd.DataFrame()
    )
    split_stats = (
        diagram_groups.groupby("split")
        .agg(samples=("sample_id", "count"), unique_diagrams=("diagram_hash", "nunique"))
        .reset_index()
        if not diagram_groups.empty
        else pd.DataFrame()
    )

    lines = [
        "# Exp1.5 Clean RC1 Benchmark",
        "",
        "## 目标",
        "",
        "把 RC1 从 baseline / audit 推进到可训练 scorer 的干净 benchmark：文本证据去掉 `solution`，hard negative 使用固定负样本数，AI2D 图像评测过滤 same-diagram wrong image。",
        "",
        "## 产物",
        "",
        "- `rc1_text_benchmark_pairs.csv`：文本 evidence alignment pair 数据，可直接用于训练/评测 scorer。",
        "- `rc1_visual_benchmark_pairs.csv`：AI2D diagram-level image pair 数据，已过滤同 diagram 负例。",
        "- `diagram_groups.csv`：AI2D diagram hash、重复组大小和 split。",
        "- `text_pair_metrics.csv` / `visual_pair_metrics.csv`：固定候选池上的 baseline 指标。",
        "",
        "## 文本 Benchmark 规模",
        "",
        df_to_markdown(text_stats),
        "",
        "## 文本 Pair 数量",
        "",
        df_to_markdown(text_pair_counts),
        "",
        "## 文本 Test 指标",
        "",
        df_to_markdown(
            text_test[
                [
                    "dataset",
                    "negative_strategy",
                    "model",
                    "n_queries",
                    "candidate_pool_size_mean",
                    "recall_at_1",
                    "mrr",
                    "top1_error_rate",
                ]
            ]
            if not text_test.empty
            else text_test
        ),
        "",
        "## 图像 Benchmark 规模",
        "",
        df_to_markdown(visual_stats),
        "",
        "## AI2D Diagram Split",
        "",
        df_to_markdown(split_stats),
        "",
        "## 图像 Pair 数量",
        "",
        df_to_markdown(visual_pair_counts),
        "",
        "## 图像 Test 指标",
        "",
        df_to_markdown(
            visual_test[
                [
                    "dataset",
                    "negative_strategy",
                    "model",
                    "n_queries",
                    "candidate_pool_size_mean",
                    "recall_at_1",
                    "mrr",
                    "top1_error_rate",
                ]
            ]
            if not visual_test.empty
            else visual_test
        ),
        "",
        "## 工作性结论",
        "",
        "- RC1 已有干净 benchmark 入口，后续 scorer 不应再使用含 `solution` 的文本 evidence 作为主结果。",
        "- 文本侧 split 按 evidence id 划分，图像侧 split 按 diagram hash 划分；这比 sample 随机切分更适合验证未见证据泛化。",
        "- 当前严格同 split 文本候选在 200 条样例上偏容易，TF-IDF / BM25 测试指标接近满分；它只能作为数据构造和训练入口，不能作为方法提升结论。",
        "- TQA / CK12 当前仍受公开 instruction 样例唯一 evidence 过少限制，只能作为流程验证；主结论应先放在 ScienceQA 和 AI2D。",
        "- 下一步可以训练一个轻量 evidence alignment scorer，并和 TF-IDF / BM25 / CLIP / SigLIP 在同一 clean benchmark 上对比。",
        "",
    ]
    (cfg.report_dir / "run_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/exp1_5_clean_rc1_benchmark.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    cfg.report_dir.mkdir(parents=True, exist_ok=True)

    data = load_samples(cfg.input_samples)
    text_pairs, text_stats = build_text_pairs(data, cfg)
    text_metrics = evaluate_text_pairs(text_pairs, cfg)

    manifest = load_ai2d_manifest(cfg)
    visual_pairs, visual_stats = build_visual_pairs(data, manifest, cfg)
    visual_metrics = evaluate_visual_pairs(visual_pairs, manifest, cfg)

    diagram_groups = manifest[
        [
            "dataset",
            "sample_id",
            "image_ref",
            "local_image_path",
            "diagram_hash",
            "diagram_group_size",
            "split",
        ]
    ].copy()

    text_pairs.to_csv(cfg.report_dir / "rc1_text_benchmark_pairs.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    text_stats.to_csv(cfg.report_dir / "text_benchmark_stats.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    text_metrics.to_csv(cfg.report_dir / "text_pair_metrics.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    visual_pairs.to_csv(cfg.report_dir / "rc1_visual_benchmark_pairs.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    visual_stats.to_csv(cfg.report_dir / "visual_benchmark_stats.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    visual_metrics.to_csv(cfg.report_dir / "visual_pair_metrics.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    diagram_groups.to_csv(cfg.report_dir / "diagram_groups.csv", index=False, quoting=csv.QUOTE_MINIMAL)

    if Path("docs/templates/experiment-run.md").exists():
        shutil.copyfile("docs/templates/experiment-run.md", cfg.report_dir / "run_record_2026-07-01.md")
    write_run_record(cfg)
    write_summary(cfg, text_pairs, text_stats, text_metrics, visual_pairs, visual_stats, visual_metrics, diagram_groups)
    print(f"Wrote {cfg.report_dir}")


if __name__ == "__main__":
    main()
