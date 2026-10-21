"""Prepare a reproducible movie sample and its existing BGE-M3 vectors.

Run from the repository root:
    python -m embedding_experiment.prepare_sample
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from embedding_experiment.cleaning import clean_plot, optional_int, split_names


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = Path(__file__).resolve().parent
REPO = "NiklasAbraham/MoviePlotEmbeddingsDataset"
REVISION = "3300dbea0b3c5891c48eb7c468116c1062ccb8a9"


def file_hash(path: Path) -> str:
    """Record the exact local input files without loading them all into memory."""
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "Data")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    if args.size < 1 or not 0 <= args.seed < 2**32:
        parser.error("Size must be positive; seed must be between 0 and 2**32 - 1.")
    output = args.output or EXPERIMENT / "data" / f"sample_{args.size}"
    if output.exists() and any(output.iterdir()):
        parser.error("Output directory is not empty. Choose a new --output to preserve the existing sample.")

    # 1. Read the existing local dataset. No download or database access is needed.
    csv_path = args.data_dir / "final_dataset.csv"
    ids_path = args.data_dir / "final_dense_movie_ids.npy"
    vectors_path = args.data_dir / "final_dense_embeddings.npy"
    movies = pd.read_csv(csv_path, low_memory=False, dtype={"movie_id": "string"})
    original_ids = np.load(ids_path, allow_pickle=False)
    original_vectors = np.load(vectors_path, mmap_mode="r", allow_pickle=False)
    if original_ids.ndim != 1 or original_vectors.shape != (len(original_ids), 1024):
        raise ValueError("Expected aligned movie IDs and a (N, 1024) embedding array.")
    if len(set(original_ids)) != len(original_ids):
        raise ValueError("The embedding ID file contains duplicate movie IDs.")
    if movies["movie_id"].dropna().duplicated().any():
        raise ValueError("The CSV contains duplicate movie IDs. Resolve them before sampling.")
    id_to_vector_row = {movie_id: index for index, movie_id in enumerate(original_ids)}

    # 2. Clean and check eligible records before selecting the sample.
    source_count = len(movies)
    movies["plot_original"] = movies["plot"]
    movies["title"] = movies["title"].fillna("").str.strip()
    movies["plot"] = movies["plot"].fillna("").map(clean_plot)
    has_vector = movies["movie_id"].isin(id_to_vector_row)
    has_title = movies["title"].str.len() > 0
    has_plot = movies["plot"].str.len() > 0
    eligible = movies[has_vector & has_title & has_plot].copy()
    if len(eligible) < args.size:
        raise ValueError(f"Only {len(eligible)} eligible movies; requested {args.size}.")

    # 3. Sort first, then sample with a fixed seed. Freeze this output for both models.
    eligible = eligible.sort_values("movie_id")
    sample = eligible.sample(n=args.size, random_state=args.seed).reset_index(drop=True)
    sample_ids = sample["movie_id"].to_numpy(dtype=str)
    vector_rows = [id_to_vector_row[movie_id] for movie_id in sample_ids]
    sample_vectors = np.asarray(original_vectors[vector_rows], dtype=np.float32)
    norms = np.linalg.norm(sample_vectors, axis=1)
    if not np.isfinite(sample_vectors).all() or not np.all((norms >= 0.95) & (norms <= 1.05)):
        raise ValueError("The selected sample contains invalid or unexpectedly scaled vectors.")

    # 4. Use experiment-local helpers and preserve the original plot for comparison.
    records = []
    for _, row in sample.iterrows():
        source_url = row.wikipedia_link
        if not isinstance(source_url, str) or not source_url.strip():
            source_url = f"https://www.wikidata.org/wiki/{row.movie_id}"
        records.append({
            "movie_id": row.movie_id,
            "title": row.title,
            "release_year": optional_int(row.year),
            "plot_original": row.plot_original,
            "plot": row["plot"],
            "genres": split_names(row.genre),
            "actors": split_names(row.actors),
            "directors": split_names(row.directors),
            "runtime_minutes": optional_int(row.duration),
            "source_url": source_url.strip(),
            "original_embedding_row": id_to_vector_row[row.movie_id],
        })

    # 5. Save human-readable data and machine-readable arrays in the same ID order.
    output.mkdir(parents=True, exist_ok=True)
    (output / "sample_movies.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    csv_records = pd.DataFrame(records)
    for column in ("genres", "actors", "directors"):
        csv_records[column] = csv_records[column].map(lambda names: json.dumps(names, ensure_ascii=False))
    csv_records.to_csv(output / "sample_movies.csv", index=False, encoding="utf-8-sig")
    np.save(output / "movie_ids.npy", sample_ids, allow_pickle=False)
    np.save(output / "bge_m3_precomputed.npy", sample_vectors, allow_pickle=False)

    manifest = {
        "stage": "sample_preparation_only",
        "dataset_repo": REPO,
        "expected_dataset_revision_from_import_script": REVISION,
        "revision_note": "Local files were not independently verified against the remote revision; SHA256 identifies the exact inputs.",
        "source_files_sha256": {p.name: file_hash(p) for p in (csv_path, ids_path, vectors_path)},
        "source_count": source_count,
        "eligible_count": len(eligible),
        "excluded_count": source_count - len(eligible),
        "failed_checks_counts_may_overlap": {
            "missing_embedding_id": int((~has_vector).sum()),
            "empty_title": int((~has_title).sum()),
            "empty_plot": int((~has_plot).sum()),
        },
        "sample_size": args.size,
        "seed": args.seed,
        "sampling": "Sort eligible rows by movie_id, then pandas sample without replacement; preserve sampled order.",
        "versions": {"numpy": np.__version__, "pandas": pd.__version__},
        "cleaning": {
            "title": "Strip leading and trailing whitespace; exclude empty titles.",
            "plot": "Collapse whitespace with the shared clean_plot helper; preserve plot_original.",
            "metadata": "Use experiment-local split_names and optional_int, matching the original import rules.",
        },
        "embedding": {
            "origin": "Existing dataset vectors, not newly generated and not reproduction-verified.",
            "model_reported_by_dataset": "BAAI/bge-m3",
            "shape": list(sample_vectors.shape),
            "source_dtype": str(original_vectors.dtype),
            "saved_dtype": str(sample_vectors.dtype),
            "renormalized": False,
            "norm_min": float(norms.min()),
            "norm_max": float(norms.max()),
        },
        "alignment": "JSON/CSV record i and both NPY row i refer to the same movie_id.",
        "hard_filters": {},
        "notes": [
            "This random sample is for a pilot; relevant movies are not guaranteed for every query.",
            "Qwen encoding, BGE-M3 reproduction checks, retrieval and relevance grading have not run.",
            "Both models must search these same movies, not compare a sample with full-catalog results.",
        ],
    }
    artifact_names = ("sample_movies.json", "sample_movies.csv", "movie_ids.npy", "bge_m3_precomputed.npy")
    manifest["artifacts_sha256"] = {name: file_hash(output / name) for name in artifact_names}
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(f"Source: {source_count}; eligible: {len(eligible)}; selected: {len(records)}; seed: {args.seed}")
    print(f"Existing BGE-M3 vectors: {sample_vectors.shape}; dtype: {sample_vectors.dtype}")
    print(f"Output: {output.resolve()}")


if __name__ == "__main__":
    main()
