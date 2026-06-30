"""Exp1.4 RC1 结果审计与消融。

该脚本不提出新模型，而是审计 Exp1.1/1.2/1.3 的结论是否可靠：

- ScienceQA `solution` 是否造成答案泄漏；
- query 中 `choices/topic/skill` 的贡献有多大；
- hard negative 的提升是否只是候选池缩小造成；
- AI2D 同一 diagram 多题是否扭曲图像检索和 wrong-image 结果。
"""

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
from PIL import Image

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
LABEL_RE = re.compile(r"(?is)(hint|lecture|solution|lesson):")


DEFAULT_CONFIG: dict[str, Any] = {
    "paths": {
        "report_dir": "reports/exp1_4_rc1_audit",
        "input_samples": [
            "data/educational_mm/schema_samples/scienceqa_schema_sample.csv",
            "data/educational_mm/schema_samples/tqa_ck12_schema_sample.csv",
            "data/educational_mm/schema_samples/ai2d_schema_sample.csv",
        ],
        "ai2d_image_manifest": "reports/exp1_3_visual_evidence_retrieval/ai2d_image_manifest.csv",
        "ai2d_image_rankings": "reports/exp1_3_visual_evidence_retrieval/image_rankings.csv",
        "ai2d_wrong_image_eval": "reports/exp1_3_visual_evidence_retrieval/wrong_image_eval.csv",
    },
    "text_audit": {
        "datasets": ["scienceqa", "tqa_ck12"],
        "query_variants": ["question_only", "question_choices", "question_choices_topic_skill"],
        "evidence_variants": ["full", "no_solution", "hint_lecture", "solution_only"],
        "min_evidence_chars": 5,
        "top_k": [1, 5, 10],
    },
    "hard_negative_audit": {
        "datasets": ["scienceqa", "tqa_ck12"],
        "strategies": ["random", "same_subject", "same_topic", "same_skill"],
        "fixed_negatives": [1, 2],
        "query_variant": "question_choices_topic_skill",
        "evidence_variant": "full",
        "random_seed": 42,
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
    ai2d_image_rankings: Path
    ai2d_wrong_image_eval: Path
    text_datasets: list[str]
    query_variants: list[str]
    evidence_variants: list[str]
    min_evidence_chars: int
    top_k: list[int]
    hard_negative_datasets: list[str]
    hard_negative_strategies: list[str]
    fixed_negatives: list[int]
    hard_negative_query_variant: str
    hard_negative_evidence_variant: str
    random_seed: int
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
        print("PyYAML is not installed; using built-in default Exp1.4 config.")
    paths = raw["paths"]
    text_audit = raw["text_audit"]
    hard_negative = raw["hard_negative_audit"]
    tfidf = raw["models"]["tfidf"]
    bm25 = raw["models"]["bm25"]
    ngram_range = tuple(int(x) for x in tfidf["ngram_range"])
    return Config(
        report_dir=Path(paths["report_dir"]),
        input_samples=[Path(p) for p in paths["input_samples"]],
        ai2d_image_manifest=Path(paths["ai2d_image_manifest"]),
        ai2d_image_rankings=Path(paths["ai2d_image_rankings"]),
        ai2d_wrong_image_eval=Path(paths["ai2d_wrong_image_eval"]),
        text_datasets=list(text_audit["datasets"]),
        query_variants=list(text_audit["query_variants"]),
        evidence_variants=list(text_audit["evidence_variants"]),
        min_evidence_chars=int(text_audit["min_evidence_chars"]),
        top_k=sorted(int(k) for k in text_audit["top_k"]),
        hard_negative_datasets=list(hard_negative["datasets"]),
        hard_negative_strategies=list(hard_negative["strategies"]),
        fixed_negatives=[int(x) for x in hard_negative["fixed_negatives"]],
        hard_negative_query_variant=str(hard_negative["query_variant"]),
        hard_negative_evidence_variant=str(hard_negative["evidence_variant"]),
        random_seed=int(hard_negative["random_seed"]),
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


def normalize_for_match(value: Any) -> str:
    return normalize_text(value).lower()


def evidence_id(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


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
    return {label: "\n".join(parts) for label, parts in segments.items()}


def evidence_variant_text(text: str, variant: str) -> str:
    text = normalize_text(text)
    segments = parse_labeled_segments(text)
    if variant == "full":
        return text
    if variant == "no_solution":
        if not segments:
            return text
        parts = [value for label, value in segments.items() if label != "solution"]
        return normalize_text("\n".join(parts))
    if variant == "hint_lecture":
        parts = [segments.get("hint", ""), segments.get("lecture", "")]
        return normalize_text("\n".join(part for part in parts if part))
    if variant == "solution_only":
        return normalize_text(segments.get("solution", ""))
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
    return " ".join(normalize_text(row.get(col, "")) for col in columns if normalize_text(row.get(col, "")))


def load_samples(paths: list[Path]) -> pd.DataFrame:
    frames = []
    for path in paths:
        data = pd.read_csv(path)
        data["source_file"] = str(path)
        frames.append(data)
    data = pd.concat(frames, ignore_index=True, sort=False)
    for column in ["dataset", "sample_id", "subject", "topic", "skill", "question", "choices", "answer", "text_context", "image_ref"]:
        if column in data.columns:
            data[column] = data[column].fillna("").astype(str)
    return data


def build_tfidf_vocab(texts: list[str], cfg: Config) -> tuple[dict[str, int], Counter[str]]:
    doc_freq: Counter[str] = Counter()
    for text in texts:
        doc_freq.update(set(text_terms(text, cfg.tfidf_ngram_range)))
    terms = [term for term, df in doc_freq.items() if df >= cfg.tfidf_min_df]
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


def score_tfidf(eval_rows: pd.DataFrame, corpus: pd.DataFrame, cfg: Config) -> np.ndarray:
    corpus_texts = corpus["evidence_text"].tolist()
    query_texts = eval_rows["query_text"].tolist()
    vocab, doc_freq = build_tfidf_vocab(corpus_texts, cfg)
    corpus_matrix = transform_tfidf(corpus_texts, vocab, doc_freq, len(corpus_texts), cfg)
    query_matrix = transform_tfidf(query_texts, vocab, doc_freq, len(corpus_texts), cfg)
    return query_matrix @ corpus_matrix.T


def bm25_scores(query: str, tokenized_docs: list[list[str]], doc_freq: Counter[str], avgdl: float, cfg: Config) -> np.ndarray:
    query_terms = tokenize(query)
    if not query_terms or not tokenized_docs:
        return np.zeros(len(tokenized_docs), dtype=float)
    n_docs = len(tokenized_docs)
    scores = np.zeros(n_docs, dtype=float)
    for term, qf in Counter(query_terms).items():
        df = doc_freq.get(term, 0)
        if df == 0:
            continue
        idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
        for idx, doc in enumerate(tokenized_docs):
            tf = doc.count(term)
            if tf == 0:
                continue
            dl = len(doc)
            denom = tf + cfg.bm25_k1 * (1 - cfg.bm25_b + cfg.bm25_b * dl / avgdl) if avgdl else tf + cfg.bm25_k1
            scores[idx] += idf * (tf * (cfg.bm25_k1 + 1) / denom) * qf
    return scores


def score_bm25(eval_rows: pd.DataFrame, corpus: pd.DataFrame, cfg: Config) -> np.ndarray:
    tokenized_docs = [tokenize(text) for text in corpus["evidence_text"]]
    doc_freq: Counter[str] = Counter()
    for doc in tokenized_docs:
        doc_freq.update(set(doc))
    avgdl = float(np.mean([len(doc) for doc in tokenized_docs])) if tokenized_docs else 0.0
    rows = [bm25_scores(query, tokenized_docs, doc_freq, avgdl, cfg) for query in eval_rows["query_text"]]
    return np.vstack(rows) if rows else np.empty((0, len(corpus)))


def rank_from_scores(scores: np.ndarray) -> np.ndarray:
    return np.lexsort((np.arange(len(scores)), -scores))


def prepare_eval_rows(data: pd.DataFrame, dataset: str, evidence_variant: str, query_variant: str, cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    subset = data[data["dataset"] == dataset].copy()
    subset["evidence_text"] = subset["text_context"].map(lambda text: evidence_variant_text(text, evidence_variant))
    subset["query_text"] = subset.apply(lambda row: make_query(row, query_variant), axis=1)
    eval_rows = subset[(subset["evidence_text"].str.len() >= cfg.min_evidence_chars) & (subset["query_text"].str.len() > 0)].copy()
    eval_rows["evidence_id"] = eval_rows["evidence_text"].map(evidence_id)
    corpus = (
        eval_rows[["evidence_id", "evidence_text", "dataset", "subject", "topic", "skill", "sample_id"]]
        .drop_duplicates("evidence_id")
        .reset_index(drop=True)
    )
    return eval_rows.reset_index(drop=True), corpus


def evaluate_scores(eval_rows: pd.DataFrame, corpus: pd.DataFrame, scores: np.ndarray, cfg: Config) -> dict[str, float]:
    corpus_ids = corpus["evidence_id"].tolist()
    hits = {k: 0 for k in cfg.top_k}
    rr_sum = 0.0
    ranks = []
    for row_idx, row in eval_rows.iterrows():
        ranking = rank_from_scores(scores[row_idx])
        ranked_ids = [corpus_ids[idx] for idx in ranking]
        target = row["evidence_id"]
        rank = ranked_ids.index(target) + 1 if target in ranked_ids else None
        if rank is None:
            continue
        ranks.append(rank)
        rr_sum += 1.0 / rank
        for k in cfg.top_k:
            if rank <= k:
                hits[k] += 1
    n = len(eval_rows)
    metrics: dict[str, float] = {"n_queries": float(n), "n_corpus": float(len(corpus)), "mrr": rr_sum / n if n else 0.0}
    for k in cfg.top_k:
        metrics[f"recall_at_{k}"] = hits[k] / n if n else 0.0
    metrics["mean_rank"] = float(np.mean(ranks)) if ranks else 0.0
    return metrics


def run_text_ablation(data: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for dataset in cfg.text_datasets:
        for evidence_variant in cfg.evidence_variants:
            for query_variant in cfg.query_variants:
                eval_rows, corpus = prepare_eval_rows(data, dataset, evidence_variant, query_variant, cfg)
                if eval_rows.empty or len(corpus) < 2:
                    rows.append(
                        {
                            "dataset": dataset,
                            "evidence_variant": evidence_variant,
                            "query_variant": query_variant,
                            "model": "skipped",
                            "reason": "empty eval rows or corpus < 2",
                            "n_queries": len(eval_rows),
                            "n_corpus": len(corpus),
                        }
                    )
                    continue
                model_scores = {"tfidf": score_tfidf(eval_rows, corpus, cfg), "bm25": score_bm25(eval_rows, corpus, cfg)}
                for model, scores in model_scores.items():
                    metrics = evaluate_scores(eval_rows, corpus, scores, cfg)
                    rows.append(
                        {
                            "dataset": dataset,
                            "evidence_variant": evidence_variant,
                            "query_variant": query_variant,
                            "model": model,
                            "reason": "",
                            **metrics,
                        }
                    )
    return pd.DataFrame(rows)


def correct_option(row: pd.Series) -> str:
    answer = normalize_text(row.get("answer", ""))
    choices = [part.strip() for part in str(row.get("choices", "")).split(" | ") if part.strip()]
    if not answer:
        return ""
    if answer.isdigit():
        idx = int(answer)
        return choices[idx] if 0 <= idx < len(choices) else ""
    if ":" in answer:
        return answer.split(":", 1)[1].strip()
    return answer


def run_leakage_audit(data: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for dataset in cfg.text_datasets:
        subset = data[data["dataset"] == dataset].copy()
        for evidence_variant in cfg.evidence_variants:
            evidence = subset["text_context"].map(lambda text: evidence_variant_text(text, evidence_variant))
            eval_subset = subset[evidence.str.len() >= cfg.min_evidence_chars].copy()
            eval_evidence = evidence[evidence.str.len() >= cfg.min_evidence_chars]
            if eval_subset.empty:
                rows.append(
                    {
                        "dataset": dataset,
                        "evidence_variant": evidence_variant,
                        "n_rows": 0,
                        "unique_evidence": 0,
                        "duplicate_groups": 0,
                        "max_duplicate_group": 0,
                        "correct_option_in_evidence_rate": 0.0,
                        "any_option_in_evidence_rate": 0.0,
                    }
                )
                continue
            correct_hits = []
            any_hits = []
            for idx, row in eval_subset.iterrows():
                evidence_text = normalize_for_match(eval_evidence.loc[idx])
                option = normalize_for_match(correct_option(row))
                options = [normalize_for_match(part) for part in str(row.get("choices", "")).split(" | ") if part.strip()]
                correct_hits.append(bool(option) and option in evidence_text)
                any_hits.append(any(bool(part) and part in evidence_text for part in options))
            counts = eval_evidence.map(normalize_text).value_counts()
            rows.append(
                {
                    "dataset": dataset,
                    "evidence_variant": evidence_variant,
                    "n_rows": len(eval_subset),
                    "unique_evidence": int(counts.size),
                    "duplicate_groups": int((counts > 1).sum()),
                    "max_duplicate_group": int(counts.max()) if not counts.empty else 0,
                    "correct_option_in_evidence_rate": float(np.mean(correct_hits)) if correct_hits else 0.0,
                    "any_option_in_evidence_rate": float(np.mean(any_hits)) if any_hits else 0.0,
                }
            )
    return pd.DataFrame(rows)


def stable_sample(indices: list[int], limit: int, key: str, seed: int) -> list[int]:
    if len(indices) <= limit:
        return sorted(indices)
    ranked = sorted(indices, key=lambda idx: hashlib.sha1(f"{seed}|{key}|{idx}".encode("utf-8")).hexdigest())
    return sorted(ranked[:limit])


def negative_indices(strategy: str, row: pd.Series, corpus: pd.DataFrame, target_idx: int) -> list[int]:
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
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    return [int(idx) for idx in corpus.index[mask]]


def eligible_common_rows(eval_rows: pd.DataFrame, corpus: pd.DataFrame, fixed_negatives: int, strategies: list[str]) -> list[int]:
    evidence_to_idx = {evidence_id_: idx for idx, evidence_id_ in enumerate(corpus["evidence_id"])}
    eligible = []
    for row_idx, row in eval_rows.iterrows():
        target_idx = evidence_to_idx.get(row["evidence_id"])
        if target_idx is None:
            continue
        if all(len(negative_indices(strategy, row, corpus, target_idx)) >= fixed_negatives for strategy in strategies):
            eligible.append(int(row_idx))
    return eligible


def evaluate_equalized_pool(
    eval_rows: pd.DataFrame,
    corpus: pd.DataFrame,
    scores: np.ndarray,
    strategy: str,
    fixed_negatives: int,
    eligible_rows: list[int],
    cfg: Config,
) -> dict[str, float]:
    evidence_to_idx = {evidence_id_: idx for idx, evidence_id_ in enumerate(corpus["evidence_id"])}
    hits = {k: 0 for k in cfg.top_k}
    rr_sum = 0.0
    margins = []
    for row_idx in eligible_rows:
        row = eval_rows.iloc[row_idx]
        target_idx = evidence_to_idx[row["evidence_id"]]
        negatives = negative_indices(strategy, row, corpus, target_idx)
        sampled = stable_sample(negatives, fixed_negatives, f"{strategy}|{row['sample_id']}|{row_idx}", cfg.random_seed)
        candidates = [target_idx] + sampled
        ordered = sorted(candidates, key=lambda idx: (-float(scores[row_idx, idx]), idx))
        rank = ordered.index(target_idx) + 1
        rr_sum += 1.0 / rank
        for k in cfg.top_k:
            if rank <= min(k, len(candidates)):
                hits[k] += 1
        best_negative = ordered[0] if ordered[0] != target_idx else (ordered[1] if len(ordered) > 1 else None)
        if best_negative is not None:
            margins.append(float(scores[row_idx, target_idx]) - float(scores[row_idx, best_negative]))
    n = len(eligible_rows)
    out: dict[str, float] = {
        "n_queries": float(n),
        "fixed_negatives": float(fixed_negatives),
        "mrr": rr_sum / n if n else 0.0,
        "top1_error_rate": 1.0 - (hits[1] / n) if n else 0.0,
        "mean_positive_margin": float(np.mean(margins)) if margins else 0.0,
    }
    for k in cfg.top_k:
        out[f"recall_at_{k}"] = hits[k] / n if n else 0.0
    return out


def run_hard_negative_equalized(data: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for dataset in cfg.hard_negative_datasets:
        eval_rows, corpus = prepare_eval_rows(
            data,
            dataset,
            cfg.hard_negative_evidence_variant,
            cfg.hard_negative_query_variant,
            cfg,
        )
        if eval_rows.empty or len(corpus) < 2:
            continue
        model_scores = {"tfidf": score_tfidf(eval_rows, corpus, cfg), "bm25": score_bm25(eval_rows, corpus, cfg)}
        for fixed_negatives in cfg.fixed_negatives:
            eligible = eligible_common_rows(eval_rows, corpus, fixed_negatives, cfg.hard_negative_strategies)
            for model, scores in model_scores.items():
                for strategy in cfg.hard_negative_strategies:
                    metrics = evaluate_equalized_pool(eval_rows, corpus, scores, strategy, fixed_negatives, eligible, cfg)
                    rows.append(
                        {
                            "dataset": dataset,
                            "model": model,
                            "strategy": strategy,
                            "common_subset": True,
                            **metrics,
                        }
                    )
    return pd.DataFrame(rows)


def image_hash(path: str) -> str:
    image = Image.open(path).convert("RGB")
    return hashlib.sha1(image.tobytes()).hexdigest()


def run_visual_audit(cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not (cfg.ai2d_image_manifest.exists() and cfg.ai2d_image_rankings.exists()):
        return pd.DataFrame(), pd.DataFrame()
    manifest = pd.read_csv(cfg.ai2d_image_manifest)
    manifest = manifest[manifest["status"] == "cached"].copy()
    manifest["diagram_hash"] = manifest["local_image_path"].map(image_hash)
    hash_by_ref = dict(zip(manifest["image_ref"], manifest["diagram_hash"]))
    hash_by_sample = dict(zip(manifest["sample_id"], manifest["diagram_hash"]))

    duplicate_counts = manifest["diagram_hash"].value_counts()
    duplicate_summary = pd.DataFrame(
        [
            {
                "cached_images": len(manifest),
                "unique_diagram_hashes": int(duplicate_counts.size),
                "duplicate_groups": int((duplicate_counts > 1).sum()),
                "images_in_duplicate_groups": int(duplicate_counts[duplicate_counts > 1].sum()),
                "max_duplicate_group": int(duplicate_counts.max()) if not duplicate_counts.empty else 0,
            }
        ]
    )

    rankings = pd.read_csv(cfg.ai2d_image_rankings)
    metric_rows = []
    for model, group in rankings.groupby("model"):
        hits = {1: 0, 5: 0, 10: 0}
        rr_at10 = 0.0
        for _, row in group.iterrows():
            target_hash = hash_by_ref.get(row["image_ref"])
            top_refs = json.loads(row["top_image_refs"])
            ranks = [idx + 1 for idx, ref in enumerate(top_refs) if hash_by_ref.get(ref) == target_hash]
            rank = ranks[0] if ranks else None
            if rank:
                rr_at10 += 1.0 / rank
                for k in hits:
                    hits[k] += rank <= k
        n = len(group)
        metric_rows.append(
            {
                "model": model,
                "n_queries": n,
                "diagram_group_recall_at_1": hits[1] / n if n else 0.0,
                "diagram_group_recall_at_5": hits[5] / n if n else 0.0,
                "diagram_group_recall_at_10": hits[10] / n if n else 0.0,
                "diagram_group_mrr_at_10": rr_at10 / n if n else 0.0,
            }
        )
    diagram_metrics = pd.DataFrame(metric_rows)
    for key, value in duplicate_summary.iloc[0].items():
        diagram_metrics[key] = value

    wrong_metrics = pd.DataFrame()
    if cfg.ai2d_wrong_image_eval.exists():
        wrong = pd.read_csv(cfg.ai2d_wrong_image_eval)
        wrong["same_exact_diagram"] = wrong.apply(
            lambda row: hash_by_sample.get(row["sample_id"]) == hash_by_sample.get(row["negative_sample_id"]),
            axis=1,
        )
        rows = []
        for (model, strategy), group in wrong.groupby(["model", "strategy"]):
            nondup = group[~group["same_exact_diagram"]]
            rows.append(
                {
                    "model": model,
                    "strategy": strategy,
                    "pairs": len(group),
                    "same_diagram_pairs": int(group["same_exact_diagram"].sum()),
                    "confusion_rate_all_pairs": float(group["wrong_image_confused"].mean()) if len(group) else 0.0,
                    "confusion_rate_nonduplicate_pairs": float(nondup["wrong_image_confused"].mean()) if len(nondup) else 0.0,
                    "nonduplicate_pairs": len(nondup),
                }
            )
        wrong_metrics = pd.DataFrame(rows)
    return diagram_metrics, wrong_metrics


def df_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_无记录。_"
    view = df.fillna("").copy()
    for col in view.columns:
        if view[col].dtype.kind == "f":
            view[col] = view[col].map(lambda x: f"{x:.4f}")
    view = view.astype(str)
    headers = list(view.columns)
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for _, row in view.iterrows():
        safe = [str(row[col]).replace("\n", "<br>").replace("|", "\\|") for col in headers]
        lines.append("| " + " | ".join(safe) + " |")
    return "\n".join(lines)


def write_summary(
    cfg: Config,
    leakage: pd.DataFrame,
    text_metrics: pd.DataFrame,
    hard_negative_equalized: pd.DataFrame,
    diagram_metrics: pd.DataFrame,
    wrong_metrics: pd.DataFrame,
) -> None:
    cfg.report_dir.mkdir(parents=True, exist_ok=True)

    scienceqa_tfidf = text_metrics[
        (text_metrics["dataset"] == "scienceqa")
        & (text_metrics["model"] == "tfidf")
        & (text_metrics["query_variant"] == "question_choices_topic_skill")
        & (text_metrics["reason"].fillna("") == "")
    ][["evidence_variant", "n_queries", "n_corpus", "recall_at_1", "mrr"]]
    query_ablation = text_metrics[
        (text_metrics["dataset"] == "scienceqa")
        & (text_metrics["model"] == "tfidf")
        & (text_metrics["evidence_variant"] == "no_solution")
        & (text_metrics["reason"].fillna("") == "")
    ][["query_variant", "n_queries", "n_corpus", "recall_at_1", "mrr"]]
    equalized_view = hard_negative_equalized[
        (hard_negative_equalized["dataset"] == "scienceqa")
        & (hard_negative_equalized["model"] == "tfidf")
        & (hard_negative_equalized["fixed_negatives"] == 1)
    ][["strategy", "n_queries", "fixed_negatives", "recall_at_1", "mrr", "top1_error_rate"]]

    lines = [
        "# Exp1.4 RC1 审计与消融",
        "",
        "## 目标",
        "",
        "在进入 RC2 之前，审计 RC1 结果是否受到答案泄漏、字段选择、候选池大小和重复图像的影响。",
        "",
        "## 审计结论",
        "",
        "- 当前 RC1 结果应表述为 baseline / evaluation audit，不应表述为已完成训练后的方法提升。",
        "- ScienceQA `solution` 会带来明显答案泄漏风险，必须使用 `no_solution` 或更干净的证据字段重跑主结果。",
        "- hard negative 的指标必须在固定候选池大小和共同 query 子集上解释，否则不能和 full-corpus baseline 直接对比。",
        "- AI2D 需要按 diagram hash 去重评估；同一张 diagram 的不同题不能互相当 wrong image。",
        "",
        "## Evidence 泄漏与重复",
        "",
        df_to_markdown(leakage),
        "",
        "## ScienceQA Evidence 消融",
        "",
        df_to_markdown(scienceqa_tfidf),
        "",
        "## ScienceQA Query 消融",
        "",
        df_to_markdown(query_ablation),
        "",
        "## 等大小 Hard Negative 审计",
        "",
        df_to_markdown(equalized_view),
        "",
        "## AI2D Diagram 去重审计",
        "",
        df_to_markdown(diagram_metrics),
        "",
        "## AI2D Wrong-image 去重审计",
        "",
        df_to_markdown(wrong_metrics),
        "",
        "## 复查原因",
        "",
        "1. ScienceQA 文本 evidence 的高指标一部分来自 `solution` 字段，属于数据构造导致的泄漏风险。",
        "2. Exp1.2 random hard negative 指标高于 Exp1.1，主要因为候选池从完整 corpus 缩小为 `1 + N` 候选，不是模型训练提升。",
        "3. TQA / CK12 的文本 evidence 只有少量唯一 lesson/instruction，当前只能作为流程连通性验证。",
        "4. AI2D 多题共用同一 diagram，sample-level 图像检索会误罚同图不同题，wrong-image 也会混入实际同图样本。",
        "",
        "## 迭代优化",
        "",
        "1. 将 RC1 主文本实验切换到 `no_solution` evidence。",
        "2. 将 query 设置拆分为 `question_only`、`question_choices`、`question_choices_topic_skill`，论文中不要混写。",
        "3. 将 hard negative 训练/评测固定为共同 query 子集和固定负样本数。",
        "4. 将 AI2D 图像检索切换到 diagram-level positive set，并过滤 same-diagram wrong image。",
        "5. 在上述干净评测上，再训练 evidence alignment scorer。",
        "",
    ]
    (cfg.report_dir / "run_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/exp1_4_rc1_audit.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    cfg.report_dir.mkdir(parents=True, exist_ok=True)

    data = load_samples(cfg.input_samples)
    leakage = run_leakage_audit(data, cfg)
    text_metrics = run_text_ablation(data, cfg)
    hard_negative_equalized = run_hard_negative_equalized(data, cfg)
    diagram_metrics, wrong_metrics = run_visual_audit(cfg)

    leakage.to_csv(cfg.report_dir / "leakage_audit.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    text_metrics.to_csv(cfg.report_dir / "text_ablation_metrics.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    hard_negative_equalized.to_csv(cfg.report_dir / "hard_negative_equalized_metrics.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    diagram_metrics.to_csv(cfg.report_dir / "diagram_group_metrics.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    wrong_metrics.to_csv(cfg.report_dir / "wrong_image_dedup_metrics.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    write_summary(cfg, leakage, text_metrics, hard_negative_equalized, diagram_metrics, wrong_metrics)
    print(f"Wrote {cfg.report_dir}")


if __name__ == "__main__":
    main()
