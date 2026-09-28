"""Stable import; PostgREST implementation lives in adapters/."""

from .adapters.supabase import SupabaseMovieRepository

__all__ = ["SupabaseMovieRepository"]
