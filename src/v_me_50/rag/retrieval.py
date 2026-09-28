"""Reference resolution and evidence-aware candidate retrieval."""

import math

from ..errors import AmbiguousReference, InvalidRequest, ModelUnavailable, UnknownReference
from ..genres import canonical_genre
from ..models import HardFilters, Intent, Movie, RetrievalResult
from ..ports import MovieRepository, QueryEmbedder


def passes_filters(movie: Movie, filters: HardFilters) -> bool:
    if filters.min_year is not None and (movie.year is None or movie.year < filters.min_year):
        return False
    if filters.max_year is not None and (movie.year is None or movie.year > filters.max_year):
        return False
    if filters.max_runtime_minutes is not None and (
        movie.runtime_minutes is None or movie.runtime_minutes > filters.max_runtime_minutes
    ):
        return False
    if filters.excluded_genres and not movie.genres:
        return False
    return not any(
        canonical_genre(excluded) in canonical_genre(genre)
        for excluded in filters.excluded_genres for genre in movie.genres
    )


class MovieRetriever:
    def __init__(self, *, embedder: QueryEmbedder, repository: MovieRepository, candidate_limit: int = 20):
        if not 1 <= candidate_limit <= 100:
            raise ValueError("Candidate limit must be between 1 and 100.")
        self.embedder = embedder
        self.repository = repository
        self.candidate_limit = candidate_limit

    def resolve_reference(self, intent: Intent) -> Movie | None:
        if not intent.reference_title:
            return None
        matches = self.repository.find_by_title(intent.reference_title)
        if intent.reference_year is not None:
            matches = [movie for movie in matches if movie.year == intent.reference_year]
        if not matches:
            raise UnknownReference(f"Reference movie '{intent.reference_title}' was not found.")
        if len(matches) > 1:
            raise AmbiguousReference(intent.reference_title, matches)
        return matches[0]

    def search(self, intent: Intent, *, reference: Movie | None, semantic_query: str | None = None) -> RetrievalResult:
        filters = intent.hard_filters
        if filters.min_year and filters.max_year and filters.min_year > filters.max_year:
            raise InvalidRequest("Minimum year cannot exceed maximum year.")
        query = semantic_query or intent.semantic_query
        vector = self.embedder.embed_query(query)
        if len(vector) != 1024 or not all(math.isfinite(value) for value in vector) or not any(vector):
            raise ModelUnavailable("Query embedding must be a finite, nonzero 1024-dimensional vector.")
        excluded_id = reference.movie_id if reference and intent.exclude_reference_movie else None
        candidates = self.repository.search(vector, filters, exclude_movie_id=excluded_id, limit=self.candidate_limit)
        unique: dict[str, Movie] = {}
        for movie in candidates:
            if movie.movie_id != excluded_id and movie.movie_id not in unique and passes_filters(movie, filters):
                unique[movie.movie_id] = movie
        return RetrievalResult(reference=reference, candidates=list(unique.values()))

    def retrieve(self, intent: Intent) -> RetrievalResult:
        """Use an already prepared semantic query without calling an LLM."""
        reference = self.resolve_reference(intent)
        query = intent.semantic_query
        if reference and not intent.soft_preferences.prefer and query.casefold() == reference.title.casefold():
            query = reference.plot[:600]
        return self.search(intent, reference=reference, semantic_query=query)

    def close(self) -> None:
        close = getattr(self.repository, "close", None)
        if close is not None:
            close()


def retrieve_candidates(intent: Intent, *, embedder: QueryEmbedder, repository: MovieRepository,
                        candidate_limit: int = 20) -> RetrievalResult:
    return MovieRetriever(embedder=embedder, repository=repository, candidate_limit=candidate_limit).retrieve(intent)
