"""Prepare JSON batches from the pinned Hugging Face dataset.

Generated batches live under data/ and are intentionally ignored by Git.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from huggingface_hub import hf_hub_download


REPO = "NiklasAbraham/MoviePlotEmbeddingsDataset"
REVISION = "3300dbea0b3c5891c48eb7c468116c1062ccb8a9"


def split_names(value: object) -> list[str]:
    if not isinstance(value, str):
        return []
    return [name.strip() for name in value.split(",") if name.strip()]


def optional_int(value: object) -> int | None:
    if pd.isna(value):
        return None
    result = int(value)
    return result if result > 0 else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--output", type=Path, default=Path("data/import_batches"))
    args = parser.parse_args()
    if not 1 <= args.limit <= 10000 or not 1 <= args.batch_size <= 50:
        raise ValueError("Use 1–10,000 movies and batches of 1–50.")

    def file(name: str) -> str:
        return hf_hub_download(REPO, name, repo_type="dataset", revision=REVISION)

    movies = pd.read_csv(file("final_dataset.csv"), low_memory=False)
    movie_ids = np.load(file("final_dense_movie_ids.npy"))
    embeddings = np.load(file("final_dense_embeddings.npy"), mmap_mode="r")
    if len(movie_ids) != len(embeddings) or embeddings.shape[1] != 1024:
        raise ValueError("Movie IDs and 1024-dimensional vectors are not aligned.")
    if len(set(movie_ids)) != len(movie_ids) or movies.movie_id.duplicated().any():
        raise ValueError("Dataset contains duplicate movie IDs.")
    id_to_vector_row = {movie_id: row for row, movie_id in enumerate(movie_ids)}
    movies = movies[
        movies.movie_id.isin(id_to_vector_row)
        & movies.title.notna()
        & movies["plot"].notna()
        & movies["plot"].str.len().ge(80)
    ].copy()
    movies["vote_count"] = pd.to_numeric(movies.vote_count, errors="coerce").fillna(0)
    movies = movies.sort_values(["vote_count", "movie_id"], ascending=[False, True]).head(args.limit)
    args.output.mkdir(parents=True, exist_ok=True)

    batch: list[dict] = []
    manifest: list[dict] = []
    for _, row in movies.iterrows():
        vector = np.asarray(embeddings[id_to_vector_row[row.movie_id]], dtype=np.float32)
        if not np.isfinite(vector).all() or not 0.95 <= np.linalg.norm(vector) <= 1.05:
            continue
        wikipedia = row.wikipedia_link if isinstance(row.wikipedia_link, str) else None
        batch.append(
            {
                "movie_id": row.movie_id,
                "title": row.title.strip(),
                "release_year": optional_int(row.year),
                "plot": " ".join(row["plot"].split()),
                "genres": split_names(row.genre),
                "actors": split_names(row.actors),
                "directors": split_names(row.directors),
                "runtime_minutes": optional_int(row.duration),
                "source_url": wikipedia or f"https://www.wikidata.org/wiki/{row.movie_id}",
                "dataset_revision": REVISION,
                "embedding": "[" + ",".join(format(float(x), ".8g") for x in vector) + "]",
            }
        )
        if len(batch) == args.batch_size:
            index = len(manifest)
            name = f"{index:04d}.json"
            (args.output / name).write_text(json.dumps(batch, ensure_ascii=False))
            manifest.append({"file": name, "rows": len(batch), "bytes": (args.output / name).stat().st_size})
            batch = []
    if batch:
        index = len(manifest)
        name = f"{index:04d}.json"
        (args.output / name).write_text(json.dumps(batch, ensure_ascii=False))
        manifest.append({"file": name, "rows": len(batch), "bytes": (args.output / name).stat().st_size})
    (args.output / "manifest.json").write_text(
        json.dumps({"repo": REPO, "revision": REVISION, "rows": sum(x["rows"] for x in manifest), "batches": manifest}, indent=2)
    )
    print(f"Prepared {sum(x['rows'] for x in manifest)} movies in {len(manifest)} batches.")


if __name__ == "__main__":
    main()
