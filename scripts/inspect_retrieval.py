"""Inspect real retrieval from a parsed intent, without pretending to run an LLM."""

import argparse
import json
import time
from pathlib import Path

from v_me_50.errors import RepositoryUnavailable
from v_me_50.factory import create_retriever
from v_me_50.models import Intent


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
    retriever = create_retriever(candidate_limit=args.limit)
    model_load_seconds = time.perf_counter() - start
    timings: list[float] = []
    orders: list[tuple[str, ...]] = []
    try:
        for _ in range(args.runs):
            start = time.perf_counter()
            result = retriever.retrieve(intent)
            timings.append(round(time.perf_counter() - start, 3))
            orders.append(tuple(movie.movie_id for movie in result.candidates))
    except RepositoryUnavailable as exc:
        raise RuntimeError("Live Supabase retrieval failed.") from exc
    finally:
        retriever.close()
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
