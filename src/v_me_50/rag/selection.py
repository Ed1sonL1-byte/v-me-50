"""Preference-based movie selection with candidate and evidence validation."""

import json

from ..models import Intent, Movie, Recommendation, Selection
from ..ports import StructuredChatModel
from .prompts import SELECTION_PROMPT
from .structured import invoke_structured


class RecommendationSelector:
    def __init__(self, llm: StructuredChatModel):
        self.chain = SELECTION_PROMPT | llm.with_structured_output(Selection)

    def select(self, request: str, intent: Intent, reference: Movie | None,
               candidates: list[Movie]) -> list[Recommendation]:
        unique = {movie.movie_id: movie for movie in candidates}
        # Bound prompt size while keeping the full retrieved records for validation.
        context = []
        remaining = 80000
        for movie in candidates:
            record = movie.model_dump(exclude={"similarity"})
            record["actors"] = movie.actors[:20]
            record["directors"] = movie.directors[:10]
            record["plot"] = movie.plot[:min(5000, max(0, remaining - 1500))]
            size = len(json.dumps(record, ensure_ascii=False))
            if not record["plot"] or size > remaining:
                break
            context.append(record)
            remaining -= size
        listed_ids = {record["movie_id"] for record in context}
        reference_record = reference.model_dump(exclude={"similarity"}) if reference else None
        if reference_record:
            reference_record["plot"] = reference.plot[:6000]
        chosen = invoke_structured(self.chain, Selection, {
            "request": request, "intent": intent.model_dump_json(),
            "reference": json.dumps(reference_record, ensure_ascii=False),
            "candidates": json.dumps(context, ensure_ascii=False),
        })
        result: list[Recommendation] = []
        seen: set[str] = set()
        for selected in chosen.recommendations:
            movie = unique.get(selected.movie_id)
            if movie is None or movie.movie_id not in listed_ids or movie.movie_id in seen:
                continue
            quote = " ".join(selected.evidence_quote.split())
            if not quote or quote not in " ".join(movie.plot.split()):
                continue
            seen.add(movie.movie_id)
            result.append(Recommendation(
                movie_id=movie.movie_id, title=movie.title, year=movie.year, genres=movie.genres,
                explanation=selected.explanation, evidence=movie.plot, evidence_quote=quote,
                source_url=movie.source_url,
            ))
        return result
