"""Interfaces owned by the RAG module; gateway and data adapters implement them."""

from typing import Protocol

from .models import HardFilters, Movie


class MovieRepository(Protocol):
    def find_by_title(self, title: str) -> list[Movie]: ...

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
