"""Read-only PostgREST adapter for the movie catalog and pgvector RPC."""

import httpx

from .models import HardFilters, Movie


class SupabaseMovieRepository:
    def __init__(self, *, url: str, publishable_key: str, timeout: float = 30.0) -> None:
        self.client = httpx.Client(
            base_url=url.rstrip("/") + "/rest/v1/",
            timeout=timeout,
            headers={"apikey": publishable_key, "Authorization": f"Bearer {publishable_key}"},
        )

    def close(self) -> None:
        self.client.close()

    def _rpc(self, name: str, payload: dict) -> list[Movie]:
        response = self.client.post(f"rpc/{name}", json=payload)
        response.raise_for_status()
        return [Movie.model_validate(row) for row in response.json()]

    def find_by_title(self, title: str) -> list[Movie]:
        return self._rpc("find_movies_by_title", {"query_title": title})

    def search(
        self,
        embedding: list[float],
        filters: HardFilters,
        *,
        exclude_movie_id: str | None,
        limit: int,
    ) -> list[Movie]:
        return self._rpc(
            "match_movies",
            {
                "query_embedding": embedding,
                "match_count": min(max(limit, 1), 100),
                "min_release_year": filters.min_year,
                "max_release_year": filters.max_year,
                "max_runtime": filters.max_runtime_minutes,
                "excluded_genres": filters.excluded_genres,
                "excluded_movie_id": exclude_movie_id,
            },
        )
