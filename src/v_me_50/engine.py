"""Stable imports for existing backend callers; implementation lives in rag/."""

from .errors import AmbiguousReference, UnknownReference
from .rag.pipeline import RecommendationEngine
from .rag.retrieval import passes_filters, retrieve_candidates

__all__ = ["RecommendationEngine", "retrieve_candidates", "passes_filters", "AmbiguousReference", "UnknownReference"]
