"""FastAPI boundary to be mounted by the backend and protected by its gateway."""

from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .engine import AmbiguousReference, RecommendationEngine, UnknownReference
from .models import RecommendationResponse


class RecommendationRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1000)


def recommendation_router(
    engine: RecommendationEngine,
    verified_user: Callable,
) -> APIRouter:
    """The gateway team supplies verified_user; no client identity header is trusted here."""
    router = APIRouter(prefix="/v1", tags=["recommendations"])

    @router.post("/recommendations", response_model=RecommendationResponse)
    def recommend(body: RecommendationRequest, user_id: str = Depends(verified_user)) -> RecommendationResponse:
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        try:
            return engine.recommend(body.query)
        except AmbiguousReference as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": str(exc),
                    "candidates": [
                        {"movie_id": m.movie_id, "title": m.title, "year": m.year}
                        for m in exc.matches
                    ],
                },
            ) from exc
        except UnknownReference as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return router
