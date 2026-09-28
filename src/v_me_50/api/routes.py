"""Translate typed recommendation use cases and failures to HTTP."""

from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ..errors import (AmbiguousReference, ConfigurationError, InvalidModelOutput, InvalidRequest,
                      ModelUnavailable, RepositoryUnavailable, UnknownReference)
from ..models import RecommendationResponse
from ..ports import RecommendationService


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    query: str = Field(min_length=3, max_length=1000)


def recommendation_router(engine: RecommendationService, verified_user: Callable) -> APIRouter:
    """The gateway supplies verified_user; client identity headers are not trusted."""
    router = APIRouter(prefix="/v1", tags=["recommendations"])

    @router.post("/recommendations", response_model=RecommendationResponse)
    def recommend(body: RecommendationRequest, user_id: str = Depends(verified_user)) -> RecommendationResponse:
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        try:
            return engine.recommend(body.query)
        except AmbiguousReference as exc:
            raise HTTPException(status_code=422, detail={
                "message": str(exc),
                "candidates": [{"movie_id": m.movie_id, "title": m.title, "year": m.year} for m in exc.matches],
            }) from exc
        except (UnknownReference, InvalidRequest) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ConfigurationError as exc:
            raise HTTPException(status_code=503, detail="Recommendation service is not configured") from exc
        except RepositoryUnavailable as exc:
            raise HTTPException(status_code=503, detail="Movie catalog is temporarily unavailable") from exc
        except ModelUnavailable as exc:
            raise HTTPException(status_code=503, detail="Recommendation model is temporarily unavailable") from exc
        except InvalidModelOutput as exc:
            raise HTTPException(status_code=502, detail="Recommendation model returned unusable data") from exc

    return router
