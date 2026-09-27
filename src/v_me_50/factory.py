"""Server-side construction; called by the backend once secrets and auth are wired."""

import os

from langchain_openai import ChatOpenAI

from .embedding import BGEM3QueryEmbedder
from .engine import RecommendationEngine
from .supabase_repository import SupabaseMovieRepository


def create_engine() -> RecommendationEngine:
    """Requires a server-side LLM key and the project's publishable movie-read key."""
    repository = SupabaseMovieRepository(
        url=os.environ["SUPABASE_URL"],
        publishable_key=os.environ["SUPABASE_PUBLISHABLE_KEY"],
    )
    return RecommendationEngine(
        llm=ChatOpenAI(model=os.environ["OPENAI_MODEL"], temperature=0),
        embedder=BGEM3QueryEmbedder(),
        repository=repository,
    )
