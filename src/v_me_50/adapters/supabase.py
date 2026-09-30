"""Read-only PostgREST adapter; no recommendation or prompt logic."""

import httpx
import numpy as np
import re
import time
from pydantic import ValidationError

from ..errors import RepositoryUnavailable
from ..genres import database_genre_terms
from ..models import HardFilters, Movie, PersonConstraint


class SupabaseMovieRepository:
    def __init__(self, *, url: str, publishable_key: str, timeout: float = 30.0,
                 client: httpx.Client | None = None):
        self._owns_client = client is None
        headers = {"apikey": publishable_key}
        # Modern publishable keys are opaque API keys, not JWTs. Legacy anon
        # keys are JWTs and may also be used as bearer tokens.
        if not publishable_key.startswith("sb_publishable_"):
            headers["Authorization"] = f"Bearer {publishable_key}"
        self.client = client or httpx.Client(
            base_url=url.rstrip("/") + "/rest/v1/", timeout=timeout,
            headers=headers,
        )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def _read_request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Retry one transient catalog failure; all calls here are read-only."""
        for attempt in range(2):
            try:
                response = self.client.request(method, path, **kwargs)
                response.raise_for_status()
                return response
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
                if attempt or (status is not None and status not in {500, 502, 503, 504}):
                    raise
                time.sleep(0.2)
        raise AssertionError("Unreachable catalog retry state")

    def _rpc(self, name: str, payload: dict) -> list[Movie]:
        try:
            response = self._read_request("POST", f"rpc/{name}", json=payload)
            records = response.json()
            if not isinstance(records, list):
                raise ValueError("Expected movie records.")
            return [Movie.model_validate(row) for row in records]
        except (httpx.HTTPError, ValidationError, ValueError, TypeError) as exc:
            raise RepositoryUnavailable("Movie catalog query failed.") from exc

    def find_by_title(self, title: str) -> list[Movie]:
        return self._rpc("find_movies_by_title", {"query_title": title})

    def find_by_person(self, person: PersonConstraint, embedding: list[float], *, limit: int) -> list[Movie]:
        """Match cast/crew metadata first, then rank those records by plot similarity."""
        name = person.name.strip()
        if not re.fullmatch(r"[\w .'-]{2,100}", name):
            return []
        condition = f'cs.{{"{name}"}}'
        params = {
            "select": "movie_id,title,year:release_year,plot,genres,actors,directors,"
                      "runtime_minutes,source_url,embedding",
            "limit": str(min(max(limit, 1), 100)),
        }
        if person.role == "either":
            params["or"] = f"(actors.{condition},directors.{condition})"
        else:
            params["actors" if person.role == "actor" else "directors"] = condition
        query = np.asarray(embedding, dtype=np.float32)
        query_norm = float(np.linalg.norm(query))
        try:
            response = self._read_request("GET", "movies", params=params)
            records = response.json()
            if not isinstance(records, list):
                raise ValueError("Expected movie records.")
            matches: list[Movie] = []
            for record in records:
                movie_vector = np.fromstring(record.pop("embedding").strip("[]"), sep=",", dtype=np.float32)
                if movie_vector.shape != query.shape:
                    continue
                movie_norm = float(np.linalg.norm(movie_vector))
                if not query_norm or not movie_norm:
                    continue
                score = float(np.dot(query, movie_vector) / (query_norm * movie_norm))
                matches.append(Movie.model_validate({**record, "similarity": score}))
            return sorted(matches, key=lambda movie: movie.similarity or 0, reverse=True)
        except (httpx.HTTPError, ValidationError, ValueError, TypeError, KeyError, AttributeError) as exc:
            raise RepositoryUnavailable("Movie catalog person lookup failed.") from exc

    def search(self, embedding: list[float], filters: HardFilters, *,
               exclude_movie_id: str | None, limit: int) -> list[Movie]:
        return self._rpc("match_movies", {
            "query_embedding": embedding, "match_count": min(max(limit, 1), 100),
            "min_release_year": filters.min_year, "max_release_year": filters.max_year,
            "max_runtime": filters.max_runtime_minutes,
            "excluded_genres": database_genre_terms(filters.excluded_genres),
            "excluded_movie_id": exclude_movie_id,
        })
