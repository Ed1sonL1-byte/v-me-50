"""Qwen encoding helpers for this experiment only."""

import json
import os
from pathlib import Path


EXPERIMENT = Path(__file__).resolve().parent
QUERY_PROMPT = (
    "Instruct: Given a movie preference query, retrieve movie plots that match its themes.\n"
    "Query: "
)

# Keep model caches on D: and use only the snapshot downloaded by download_qwen.py.
# These settings must be established before importing Hugging Face libraries.
os.environ["HF_HOME"] = str(EXPERIMENT / "models" / "huggingface")
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"


def load_model(max_length: int = 8192, threads: int = 8):
    import torch
    from sentence_transformers import SentenceTransformer

    config_path = EXPERIMENT / "models" / "qwen_model.json"
    if not config_path.exists():
        raise FileNotFoundError("Run python -m embedding_experiment.download_qwen first.")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    snapshot = EXPERIMENT / config["snapshot_path"]
    torch.set_num_threads(threads)
    model = SentenceTransformer(
        str(snapshot),
        device="cpu",
        local_files_only=True,
        trust_remote_code=False,
        model_kwargs={"dtype": torch.float32},
    )
    model.max_seq_length = max_length
    if model.get_sentence_embedding_dimension() != 1024:
        raise ValueError("Expected 1024-dimensional Qwen embeddings.")
    return model, config


def encode_movies(model, plots: list[str], batch_size: int = 2):
    """Documents have no task instruction. Return vectors in input order."""
    return model.encode(
        plots,
        prompt="",
        batch_size=batch_size,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )


def encode_queries(model, queries: list[str], batch_size: int = 2):
    """Queries use a fixed movie-retrieval instruction, unlike documents."""
    return model.encode(
        queries,
        prompt=QUERY_PROMPT,
        batch_size=batch_size,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
