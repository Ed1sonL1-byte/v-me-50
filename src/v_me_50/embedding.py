"""Stable import; encoder implementation lives in adapters/."""

from .adapters.embeddings import BGEM3QueryEmbedder

__all__ = ["BGEM3QueryEmbedder"]
