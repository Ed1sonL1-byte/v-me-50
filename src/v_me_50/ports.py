"""Storage, encoder, and recommendation contracts without framework dependencies."""

from typing import Any, Protocol

from pydantic import BaseModel

from .models import HardFilters, Movie, PersonConstraint, RecommendationResponse


class MovieRepository(Protocol):
    def find_by_title(self, title: str) -> list[Movie]: ...

    def find_by_person(self, person: PersonConstraint, embedding: list[float], *, limit: int) -> list[Movie]: ...

    def search(
        self,
        embedding: list[float],
        filters: HardFilters,
        *,
        exclude_movie_id: str | None,
        limit: int,
    ) -> list[Movie]: ...


class QueryEmbedder(Protocol):
    def embed_query(self, text: str) -> list[float]: ...


class RecommendationService(Protocol):
    def recommend(self, request: str) -> RecommendationResponse: ...


class StructuredChatModel(Protocol):
    def with_structured_output(self, schema: type[BaseModel]) -> Any:
        """Return a LangChain-compatible structured-output runnable."""
        ...
