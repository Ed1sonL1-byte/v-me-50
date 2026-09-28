"""Compose the recommendation stages; no HTTP, environment, or SQL concerns."""

from collections.abc import Callable, Sequence

from ..errors import ConfigurationError, InvalidRequest
from ..models import RecommendationResponse
from ..ports import MovieRepository, QueryEmbedder, StructuredChatModel
from .intent import IntentParser
from .query import ReferenceQueryBuilder
from .retrieval import MovieRetriever
from .selection import RecommendationSelector


class RecommendationEngine:
    def __init__(self, *, llm: StructuredChatModel, embedder: QueryEmbedder, repository: MovieRepository,
                 candidate_limit: int = 20, closers: Sequence[Callable[[], None]] = ()):
        self.intent_parser = IntentParser(llm)
        self.query_builder = ReferenceQueryBuilder(llm)
        self.retriever = MovieRetriever(embedder=embedder, repository=repository, candidate_limit=candidate_limit)
        self.selector = RecommendationSelector(llm)
        self._closers = tuple(closers)
        self._closed = False

    def recommend(self, request: str) -> RecommendationResponse:
        if self._closed:
            raise ConfigurationError("The recommendation engine has shut down.")
        request = request.strip()
        if not 3 <= len(request) <= 1000:
            raise InvalidRequest("Request must contain 3 to 1000 characters.")
        intent = self.intent_parser.parse(request)
        reference = self.retriever.resolve_reference(intent)
        query = self.query_builder.build(request, intent, reference)
        retrieved = self.retriever.search(intent, reference=reference, semantic_query=query)
        reference_id = reference.movie_id if reference else None
        if not retrieved.candidates:
            return RecommendationResponse(recommendations=[], reference_movie_id=reference_id,
                                          message="No movies satisfy the available evidence and hard filters.")
        recommendations = self.selector.select(request, intent, reference, retrieved.candidates)
        return RecommendationResponse(
            recommendations=recommendations, reference_movie_id=reference_id,
            message=None if recommendations else "No evidence-supported recommendations could be produced.",
        )

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            for close in self._closers:
                close()
