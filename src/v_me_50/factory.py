"""Composition root: wire validated settings to adapters and recommendation stages."""

from .adapters.embeddings import BGEM3QueryEmbedder
from .adapters.llm import OpenAIChatModel
from .adapters.supabase import SupabaseMovieRepository
from .errors import ConfigurationError, ModelUnavailable
from .rag.pipeline import RecommendationEngine
from .rag.retrieval import MovieRetriever
from .settings import LLMSettings, RetrievalSettings


def create_retriever(settings: RetrievalSettings | None = None, *, candidate_limit: int | None = None) -> MovieRetriever:
    settings = settings or RetrievalSettings.from_env()
    repository = SupabaseMovieRepository(
        url=str(settings.supabase_url), publishable_key=settings.supabase_publishable_key.get_secret_value(),
        timeout=settings.timeout_seconds,
    )
    try:
        return MovieRetriever(
            embedder=BGEM3QueryEmbedder(settings.embedding_model), repository=repository,
            candidate_limit=settings.candidate_limit if candidate_limit is None else candidate_limit,
        )
    except Exception:
        repository.close()
        raise


def create_engine(settings: RetrievalSettings | None = None,
                  llm_settings: LLMSettings | None = None) -> RecommendationEngine:
    settings = settings or RetrievalSettings.from_env()
    llm_settings = llm_settings or LLMSettings.from_env()
    llm: OpenAIChatModel | None = None
    retriever: MovieRetriever | None = None
    try:
        llm = OpenAIChatModel(llm_settings)
        retriever = create_retriever(settings)
        return RecommendationEngine(
            llm=llm, embedder=retriever.embedder, repository=retriever.repository,
            candidate_limit=settings.candidate_limit, closers=(retriever.close, llm.close),
        )
    except Exception as exc:
        if llm is not None:
            llm.close()
        if retriever is not None:
            retriever.close()
        if isinstance(exc, (ConfigurationError, ModelUnavailable)):
            raise
        raise ConfigurationError("Could not initialize the recommendation dependencies.") from exc
