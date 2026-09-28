"""Inspect real retrieval from a parsed intent, without pretending to run an LLM."""

import argparse
import json
import os
import time
from pathlib import Path

import httpx

from v_me_50.embedding import BGEM3QueryEmbedder
from v_me_50.engine import retrieve_candidates
from v_me_50.models import Intent
from v_me_50.supabase_repository import SupabaseMovieRepository


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intent", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/retrieval-inspection.json"))
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--runs", type=int, default=1)
    args = parser.parse_args()
    if not 1 <= args.limit <= 100 or not 1 <= args.runs <= 10:
        raise ValueError("Use limit 1–100 and runs 1–10.")
    intent = Intent.model_validate_json(args.intent.read_text())
    start = time.perf_counter()
    embedder = BGEM3QueryEmbedder()
    model_load_seconds = time.perf_counter() - start
    repository = SupabaseMovieRepository(
        url=os.environ["SUPABASE_URL"],
        publishable_key=os.environ["SUPABASE_PUBLISHABLE_KEY"],
    )
    timings: list[float] = []
    orders: list[tuple[str, ...]] = []
    try:
        for _ in range(args.runs):
            start = time.perf_counter()
            result = retrieve_candidates(intent, embedder=embedder, repository=repository, candidate_limit=args.limit)
            timings.append(round(time.perf_counter() - start, 3))
            orders.append(tuple(movie.movie_id for movie in result.candidates))
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"Supabase RPC failed ({exc.response.status_code}): {exc.response.text[:1000]}") from exc
    finally:
        repository.close()
    payload = {
        "stage": "retrieval_only_no_llm_selection",
        "intent": intent.model_dump(),
        "model_load_seconds": round(model_load_seconds, 3),
        "retrieval_seconds": timings,
        "consistent_movie_ids": len(set(orders)) == 1,
        **result.model_dump(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Retrieved {len(result.candidates)} candidates; run seconds {timings} (model load {model_load_seconds:.2f}s).")
    for index, movie in enumerate(result.candidates, 1):
        print(f"{index:2}. {movie.movie_id} | {movie.title} ({movie.year}) | {movie.similarity:.4f} | {', '.join(movie.genres)}")


if __name__ == "__main__":
    main()
