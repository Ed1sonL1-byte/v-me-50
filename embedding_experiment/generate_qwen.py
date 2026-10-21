"""Generate Qwen movie embeddings for the fixed sample, without touching the app."""

import argparse
import hashlib
import json
import platform
import time
from importlib.metadata import version
from pathlib import Path

import numpy as np

from embedding_experiment.qwen_encoder import EXPERIMENT, QUERY_PROMPT, encode_movies, load_model


def file_hash(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-dir", type=Path, default=EXPERIMENT / "data" / "sample_100")
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--max-length", type=int, default=8192)
    parser.add_argument("--threads", type=int, default=8)
    args = parser.parse_args()
    if args.batch_size < 1 or args.threads < 1 or not 1 <= args.max_length <= 32768:
        parser.error("Use positive batch size and threads, and a max length between 1 and 32768.")

    sample_dir = args.sample_dir.resolve()
    output = sample_dir / "qwen"
    if output.exists() and any(output.iterdir()):
        parser.error("Qwen output already exists. Preserve this run before starting another.")
    records_path = sample_dir / "sample_movies.json"
    ids_path = sample_dir / "movie_ids.npy"
    records = json.loads(records_path.read_text(encoding="utf-8"))
    ids = np.load(ids_path, allow_pickle=False)
    if not records or ids.ndim != 1 or ids.tolist() != [row["movie_id"] for row in records]:
        raise ValueError("Sample records and movie IDs are not aligned.")
    if len(set(ids)) != len(ids):
        raise ValueError("Sample contains duplicate movie IDs.")
    plots = [row["plot"] for row in records]
    if any(not isinstance(plot, str) or not plot.strip() for plot in plots):
        raise ValueError("Every movie needs a nonempty cleaned plot.")
    input_hashes = {p.name: file_hash(p) for p in (records_path, ids_path)}

    print(f"Loading Qwen locally on CPU; sample size: {len(plots)}", flush=True)
    started = time.perf_counter()
    model, model_config = load_model(args.max_length, args.threads)
    load_seconds = time.perf_counter() - started
    print(f"Model loaded in {load_seconds:.2f}s", flush=True)

    # Check truncation explicitly. This is outside the measured encoding time.
    token_lengths = []
    for plot in plots:
        tokens = model.tokenizer(plot, truncation=False, add_special_tokens=True)["input_ids"]
        token_lengths.append(len(tokens))
    truncated_count = sum(length > args.max_length for length in token_lengths)
    print(f"Plot tokens: min={min(token_lengths)}, max={max(token_lengths)}; truncated={truncated_count}", flush=True)

    batches = []
    batch_timings = []
    encoding_start = time.perf_counter()
    for start in range(0, len(plots), args.batch_size):
        stop = min(start + args.batch_size, len(plots))
        batch_start = time.perf_counter()
        vectors = np.asarray(encode_movies(model, plots[start:stop], args.batch_size), dtype=np.float32)
        if vectors.shape != (stop - start, 1024) or not np.isfinite(vectors).all():
            raise ValueError(f"Invalid embeddings in rows {start}:{stop}.")
        if not np.allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-4, rtol=0):
            raise ValueError("Expected L2-normalized embeddings.")
        batches.append(vectors)
        elapsed = time.perf_counter() - batch_start
        batch_timings.append({"start": start, "stop": stop, "seconds": round(elapsed, 4)})
        print(f"Encoded {stop}/{len(plots)} movies; batch {elapsed:.2f}s", flush=True)
    encoding_seconds = time.perf_counter() - encoding_start
    embeddings = np.concatenate(batches, axis=0)

    # Do not attach results to a sample that changed while the model was running.
    if input_hashes != {p.name: file_hash(p) for p in (records_path, ids_path)}:
        raise ValueError("Input sample changed during encoding. Results were not saved.")
    output.mkdir(parents=True, exist_ok=True)
    vector_path = output / "movie_embeddings.npy"
    np.save(vector_path, embeddings, allow_pickle=False)
    np.save(output / "movie_ids.npy", ids, allow_pickle=False)
    np.save(output / "plot_token_lengths.npy", np.asarray(token_lengths, dtype=np.int32), allow_pickle=False)

    manifest = {
        "stage": "qwen_movie_encoding_completed",
        "model_id": model_config["model_id"],
        "model_revision": model_config["revision"],
        "sample_files_sha256": input_hashes,
        "shape": list(embeddings.shape),
        "dtype": str(embeddings.dtype),
        "input_field": "plot",
        "document_prompt": "",
        "query_prompt_for_future_retrieval": QUERY_PROMPT,
        "query_embeddings_generated": False,
        "normalize_embeddings": True,
        "pooling": str(model[1]),
        "max_length": model.max_seq_length,
        "truncation_side": model.tokenizer.truncation_side,
        "padding_side": model.tokenizer.padding_side,
        "truncated_movie_count": truncated_count,
        "token_length_min": min(token_lengths),
        "token_length_max": max(token_lengths),
        "token_length_mean": float(np.mean(token_lengths)),
        "device": str(model.device),
        "model_dtype": str(next(model.parameters()).dtype),
        "cpu": platform.processor(),
        "threads": args.threads,
        "batch_size": args.batch_size,
        "model_load_seconds": round(load_seconds, 3),
        "movie_encoding_seconds": round(encoding_seconds, 3),
        "download_seconds_recorded_separately": model_config["download_seconds"],
        "batch_timings": batch_timings,
        "versions": {name: version(name) for name in ("torch", "transformers", "sentence-transformers", "numpy")},
        "artifacts_sha256": {p.name: file_hash(p) for p in output.glob("*.npy")},
        "comparison_status": "Existing BGE-M3 vectors reused by user choice; reproduction check skipped. Retrieval and human grading have not run.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Saved {embeddings.shape} embeddings to {vector_path}", flush=True)
    print(f"Movie encoding time: {encoding_seconds:.2f}s; all rows match the fixed movie ID order.", flush=True)


if __name__ == "__main__":
    main()
