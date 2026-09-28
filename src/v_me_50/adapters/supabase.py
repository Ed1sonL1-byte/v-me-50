"""Read-only PostgREST adapter; no recommendation or prompt logic."""

import httpx
from pydantic import ValidationError

from ..errors import RepositoryUnavailable
from ..genres import database_genre_terms
from ..models import HardFilters, Movie


class SupabaseMovieRepository:
    def __init__(self, *, url: str, publishable_key: str, timeout: float = 30.0,
                 client: httpx.Client | None = None):
        self._owns_client = client is None
        self.client = client or httpx.Client(
            base_url=url.rstrip("/") + "/rest/v1/", timeout=timeout,
            headers={"apikey": publishable_key, "Authorization": f"Bearer {publishable_key}"},
        )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def _rpc(self, name: str, payload: dict) -> list[Movie]:
        try:
            response = self.client.post(f"rpc/{name}", json=payload)
            response.raise_for_status()
            records = response.json()
            if not isinstance(records, list):
                raise ValueError("Expected movie records.")
            return [Movie.model_validate(row) for row in records]
        except (httpx.HTTPError, ValidationError, ValueError, TypeError) as exc:
            raise RepositoryUnavailable("Movie catalog query failed.") from exc

    def find_by_title(self, title: str) -> list[Movie]:
        return self._rpc("find_movies_by_title", {"query_title": title})

    def search(self, embedding: list[float], filters: HardFilters, *,
               exclude_movie_id: str | None, limit: int) -> list[Movie]:
        return self._rpc("match_movies", {
            "query_embedding": embedding, "match_count": min(max(limit, 1), 100),
            "min_release_year": filters.min_year, "max_release_year": filters.max_year,
            "max_runtime": filters.max_runtime_minutes,
            "excluded_genres": database_genre_terms(filters.excluded_genres),
            "excluded_movie_id": exclude_movie_id,
        })
