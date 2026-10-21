"""Run one fixed query against both movie-vector sets with identical candidates."""

import argparse
import csv
import gc
import hashlib
import json
import random
import time
from pathlib import Path

import numpy as np

# This module sets offline cache settings before model libraries are imported.
from embedding_experiment.qwen_encoder import EXPERIMENT, QUERY_PROMPT, encode_queries, load_model


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def file_hash(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def filter_by_year(records: list[dict], filters: dict) -> list[int]:
    """Select candidates once, before either model ranks them.

    This first experiment supports year bounds only. Reject other filters rather
    than silently ignoring them. Unknown movie years fail an active year bound.
    """
    if not isinstance(filters, dict) or set(filters) - {"min_year", "max_year"}:
        raise ValueError("This experiment currently supports only min_year and max_year.")
    minimum = filters.get("min_year")
    maximum = filters.get("max_year")
    for value in (minimum, maximum):
        if value is not None and (type(value) is not int or not 1880 <= value <= 2100):
            raise ValueError("Year bounds must be integers from 1880 to 2100, or null.")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("min_year cannot exceed max_year.")
    indices = []
    for index, movie in enumerate(records):
        year = movie["release_year"]
        if minimum is not None and (year is None or year < minimum):
            continue
        if maximum is not None and (year is None or year > maximum):
            continue
        indices.append(index)
    return indices


def rank_movies(records, candidate_indices, movie_vectors, query_vector, limit):
    """Exact cosine search; normalize both sides, including the old float16 vectors."""
    query_vector = np.asarray(query_vector, dtype=np.float32)
    if query_vector.shape != (movie_vectors.shape[1],) or not np.isfinite(query_vector).all():
        raise ValueError("Invalid query vector.")
    query_norm = np.linalg.norm(query_vector)
    if query_norm == 0:
        raise ValueError("Query vector must be nonzero.")
    if not candidate_indices:
        return []
    selected = np.asarray(movie_vectors[candidate_indices], dtype=np.float32)
    norms = np.linalg.norm(selected, axis=1)
    if not np.isfinite(selected).all() or np.any(norms == 0):
        raise ValueError("Movie vectors must be finite and nonzero.")
    scores = (selected / norms[:, None]) @ (query_vector / query_norm)
    order = sorted(range(len(candidate_indices)), key=lambda i: (
        -float(scores[i]), records[candidate_indices[i]]["movie_id"]
    ))
    results = []
    for rank, position in enumerate(order[:limit], 1):
        movie = records[candidate_indices[position]]
        results.append({
            "rank": rank,
            "movie_id": movie["movie_id"],
            "title": movie["title"],
            "release_year": movie["release_year"],
            "genres": movie["genres"],
            "similarity": float(scores[position]),
            "plot": movie["plot"],
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", type=Path, default=EXPERIMENT / "queries" / "scifi_after_2000.json")
    parser.add_argument("--sample-dir", type=Path, default=EXPERIMENT / "data" / "sample_100")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--bge-model-path", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.limit <= 100:
        parser.error("Limit must be from 1 to 100.")
    query = read_json(args.query)
    text = query.get("semantic_query")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("semantic_query must be a nonempty string.")
    output = args.output or EXPERIMENT / "data" / "results" / args.query.stem
    if output.exists() and any(output.iterdir()):
        parser.error("Results already exist. Choose a new --output to preserve them.")

    sample = args.sample_dir
    records = read_json(sample / "sample_movies.json")
    ids = np.load(sample / "movie_ids.npy", allow_pickle=False)
    qwen_ids = np.load(sample / "qwen" / "movie_ids.npy", allow_pickle=False)
    if ids.tolist() != [r["movie_id"] for r in records] or not np.array_equal(ids, qwen_ids):
        raise ValueError("Movie records and both embedding ID lists must match exactly.")
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate movie IDs.")
    sample_manifest = read_json(sample / "manifest.json")
    qwen_manifest = read_json(sample / "qwen" / "manifest.json")
    for name, expected in sample_manifest["artifacts_sha256"].items():
        if file_hash(sample / name) != expected:
            raise ValueError(f"Sample changed: {name}")
    for name, expected in qwen_manifest["artifacts_sha256"].items():
        if file_hash(sample / "qwen" / name) != expected:
            raise ValueError(f"Qwen artifact changed: {name}")
    for name, expected in qwen_manifest["sample_files_sha256"].items():
        if file_hash(sample / name) != expected:
            raise ValueError(f"Qwen was encoded from a different sample: {name}")
    candidate_indices = filter_by_year(records, query.get("hard_filters", {}))
    candidate_ids = [records[i]["movie_id"] for i in candidate_indices]
    vector_files = {
        "bge_m3": sample / "bge_m3_precomputed.npy",
        "qwen": sample / "qwen" / "movie_embeddings.npy",
    }
    movie_vectors = {name: np.load(path, allow_pickle=False) for name, path in vector_files.items()}
    if any(array.shape != (len(records), 1024) for array in movie_vectors.values()):
        raise ValueError("Expected two aligned (N, 1024) arrays for this experiment.")

    print(f"Query: {text}", flush=True)
    print(f"Shared candidate set: {len(candidate_ids)}/{len(records)} movies", flush=True)
    if not candidate_ids:
        raise ValueError("No eligible movies. Adjust the query deliberately before running models.")

    # Read the existing BGE-M3 snapshot without downloading or changing its cache.
    bge_path = args.bge_model_path
    if bge_path is None:
        cache = EXPERIMENT.parent / "Data" / "huggingface-cache" / "hub" / "models--BAAI--bge-m3"
        revision = (cache / "refs" / "main").read_text().strip()
        bge_path = cache / "snapshots" / revision
    import torch
    from sentence_transformers import SentenceTransformer

    torch.set_num_threads(8)
    started = time.perf_counter()
    bge = SentenceTransformer(str(bge_path), device="cpu", local_files_only=True,
                              trust_remote_code=False, model_kwargs={"dtype": torch.float32})
    bge_load = time.perf_counter() - started
    bge.max_seq_length = 8192
    started = time.perf_counter()
    bge_query = bge.encode(text, prompt="", normalize_embeddings=True, convert_to_numpy=True)
    bge_encode = time.perf_counter() - started
    del bge
    gc.collect()

    started = time.perf_counter()
    qwen, qwen_config = load_model(qwen_manifest["max_length"], qwen_manifest["threads"])
    qwen_load = time.perf_counter() - started
    if qwen_config["revision"] != qwen_manifest["model_revision"] or QUERY_PROMPT != qwen_manifest["query_prompt_for_future_retrieval"]:
        raise ValueError("Qwen model revision or query instruction changed since movie encoding.")
    started = time.perf_counter()
    qwen_query = encode_queries(qwen, [text])[0]
    qwen_encode = time.perf_counter() - started
    del qwen
    gc.collect()

    query_vectors = {"bge_m3": bge_query, "qwen": qwen_query}
    results, search_seconds = {}, {}
    for name in query_vectors:
        started = time.perf_counter()
        results[name] = rank_movies(records, candidate_indices, movie_vectors[name], query_vectors[name], args.limit)
        search_seconds[name] = time.perf_counter() - started
    output.mkdir(parents=True, exist_ok=True)
    for name, vector in query_vectors.items():
        np.save(output / f"{name}_query.npy", np.asarray(vector, dtype=np.float32), allow_pickle=False)
    comparison = {
        "query": query,
        "query_file_sha256": file_hash(args.query),
        "candidate_movie_ids": candidate_ids,
        "candidate_count": len(candidate_ids),
        "requested_top_k": args.limit,
        "bge_query_model_revision": bge_path.name,
        "qwen_model_revision": qwen_config["revision"],
        "qwen_query_prompt": QUERY_PROMPT,
        "movie_vector_files_sha256": {name: file_hash(path) for name, path in vector_files.items()},
        "timings_seconds": {
            "bge_m3": {"load": bge_load, "query_encode": bge_encode, "search": search_seconds["bge_m3"]},
            "qwen": {"load": qwen_load, "query_encode": qwen_encode, "search": search_seconds["qwen"]},
        },
        "timing_note": "One first query after model loading; not a warmed-up speed benchmark.",
        "evaluation_status": "No human relevance judgments yet. Similarity scores across models are not quality metrics.",
        "baseline_note": "BGE-M3 movie vectors reused; historical encoding settings not reproduction-verified.",
        "results": results,
    }
    (output / "comparison.json").write_text(json.dumps(comparison, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    report = ["# Retrieval comparison: science-fiction pilot" if args.query.stem == "scifi_after_2000" else "# Retrieval comparison",
              "", f"Query: {text}", "", f"Hard filters: `{json.dumps(query.get('hard_filters', {}))}`",
              f"Shared candidate movies: {len(candidate_ids)} / {len(records)}", "",
              "Unscored pilot results. Rank is not a guarantee of relevance. Scores from different models are not directly comparable.",
              "", "| Rank | BGE-M3 movie | Year | Qwen movie | Year |", "| --- | --- | --- | --- | --- |"]
    for a, b in zip(results["bge_m3"], results["qwen"]):
        report.append(f"| {a['rank']} | {a['title'].replace('|', '/')} | {a['release_year']} | {b['title'].replace('|', '/')} | {b['release_year']} |")
    common = set(r["movie_id"] for r in results["bge_m3"]) & set(r["movie_id"] for r in results["qwen"])
    report += ["", f"Returned-list overlap: {len(common)} movies. Overlap alone does not measure relevance.",
               "", "Use blind_review.csv to independently label relevant / not relevant / insufficient evidence.",
               query.get("relevance_criterion", "Judge relevance against all semantic requirements in the query. Define the criteria before grading; mark insufficient evidence when the plot is inconclusive."),
               "This is a small random sample, not a representative benchmark. No parser or final LLM selection ran.",
               "One-shot timings are in comparison.json; do not use them as reliable model speed rankings."]
    (output / "comparison.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    # The rating sheet omits model identity, original rank, and similarity scores.
    pooled = {r["movie_id"]: r for values in results.values() for r in values}
    review = list(pooled.values())
    random.Random(42).shuffle(review)
    fields = ["semantic_query", "movie_id", "title", "release_year", "plot", "reviewer_1", "reviewer_2", "notes"]
    with (output / "blind_review.csv").open("w", encoding="utf-8-sig", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        for movie in review:
            writer.writerow({"semantic_query": text, **{key: movie[key] for key in ("movie_id", "title", "release_year", "plot")}})
    print(f"Saved results: {output}", flush=True)
    for name, rows in results.items():
        print(f"{name} Top 5:", [(r["title"], r["release_year"]) for r in rows[:5]], flush=True)


if __name__ == "__main__":
    main()
