"""Application assembly, gateway extension point, and shared engine lifetime."""

from collections.abc import Callable
from contextlib import asynccontextmanager
from threading import Lock

from fastapi import FastAPI, HTTPException

from ..errors import ConfigurationError
from ..models import RecommendationResponse
from ..ports import RecommendationService
from .routes import recommendation_router


def default_engine_factory() -> RecommendationService:
    from ..factory import create_engine
    return create_engine()


def unconfigured_auth() -> str:
    raise HTTPException(status_code=503, detail="Gateway authentication is not configured")


class LazyRecommendationService:
    """Initialize once after authentication; model loading is never done per request."""

    def __init__(self, builder: Callable[[], RecommendationService]):
        self.builder = builder
        self._engine: RecommendationService | None = None
        self._lock = Lock()
        self._closed = False

    def recommend(self, request: str) -> RecommendationResponse:
        with self._lock:
            if self._closed:
                raise ConfigurationError("The recommendation service has shut down.")
            if self._engine is None:
                self._engine = self.builder()
            engine = self._engine
        return engine.recommend(request)

    def close(self) -> None:
        with self._lock:
            self._closed = True
            if self._engine is not None:
                close = getattr(self._engine, "close", None)
                if close:
                    close()
                self._engine = None


def create_app(*, verified_user: Callable | None = None, engine: RecommendationService | None = None,
               engine_factory: Callable[[], RecommendationService] = default_engine_factory) -> FastAPI:
    owned_service = LazyRecommendationService(engine_factory) if engine is None else None
    service = owned_service if owned_service is not None else engine

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            yield
        finally:
            if owned_service is not None:
                owned_service.close()

    app = FastAPI(title="V Me 50 Recommendation API", version="0.1.0", lifespan=lifespan)
    app.include_router(recommendation_router(service, verified_user or unconfigured_auth))

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
