"""Stable contracts shared with the gateway and the recommendation API."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HardFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_year: int | None = Field(default=None, ge=1880, le=2100)
    max_year: int | None = Field(default=None, ge=1880, le=2100)
    max_runtime_minutes: int | None = Field(default=None, ge=1, le=1000)
    excluded_genres: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("excluded_genres")
    @classmethod
    def clean_genres(cls, genres: list[str]) -> list[str]:
        return [genre.strip().casefold() for genre in genres if genre.strip()]


class SoftPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prefer: list[str] = Field(default_factory=list, max_length=8)
    avoid: list[str] = Field(default_factory=list, max_length=8)


class Intent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_title: str | None = None
    semantic_query: str = Field(min_length=3, max_length=600)
    hard_filters: HardFilters = Field(default_factory=HardFilters)
    soft_preferences: SoftPreferences = Field(default_factory=SoftPreferences)
    exclude_reference_movie: bool = True


class Movie(BaseModel):
    model_config = ConfigDict(extra="forbid")

    movie_id: str
    title: str
    year: int | None = None
    plot: str
    genres: list[str] = Field(default_factory=list)
    actors: list[str] = Field(default_factory=list)
    directors: list[str] = Field(default_factory=list)
    runtime_minutes: int | None = None
    source_url: str | None = None
    similarity: float | None = None


class RetrievalResult(BaseModel):
    reference: Movie | None = None
    candidates: list[Movie]


class SelectedMovie(BaseModel):
    movie_id: str
    explanation: str = Field(min_length=1, max_length=1000)


class Selection(BaseModel):
    recommendations: list[SelectedMovie] = Field(max_length=5)


class Recommendation(BaseModel):
    movie_id: str
    title: str
    year: int | None
    genres: list[str]
    explanation: str
    evidence: str
    source_url: str | None


class RecommendationResponse(BaseModel):
    recommendations: list[Recommendation]
    reference_movie_id: str | None = None
    message: str | None = None
