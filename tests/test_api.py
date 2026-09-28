from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import pytest

from v_me_50.api import recommendation_router
from v_me_50.models import RecommendationResponse
from v_me_50.errors import ConfigurationError, InvalidModelOutput, ModelUnavailable, RepositoryUnavailable


class StubEngine:
    def recommend(self, request: str) -> RecommendationResponse:
        assert request == "Family drama"
        return RecommendationResponse(recommendations=[], message="No candidates")


def test_route_uses_verified_principal_dependency():
    app = FastAPI()

    def verified_user():
        return "user-123"

    app.include_router(recommendation_router(StubEngine(), verified_user))
    response = TestClient(app).post("/v1/recommendations", json={"query": "Family drama"})
    assert response.status_code == 200
    assert response.json()["message"] == "No candidates"


def test_route_rejects_missing_principal():
    app = FastAPI()

    def verified_user():
        raise HTTPException(status_code=401, detail="Authentication required")

    app.include_router(recommendation_router(StubEngine(), verified_user))
    response = TestClient(app).post("/v1/recommendations", json={"query": "Family drama"})
    assert response.status_code == 401


def test_application_starts_without_loading_models_and_fails_closed():
    from v_me_50.app import create_app
    calls = []
    def builder():
        calls.append("initialized")
        return StubEngine()
    with TestClient(create_app(engine_factory=builder)) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert "/v1/recommendations" in client.get("/openapi.json").json()["paths"]
        assert client.post("/v1/recommendations", json={"query": "Family drama"}).status_code == 503
    assert calls == []


def test_application_reuses_and_closes_its_engine():
    from v_me_50.app import create_app
    calls = []
    class Engine(StubEngine):
        def close(self):
            calls.append("closed")
    def builder():
        calls.append("initialized")
        return Engine()
    with TestClient(create_app(verified_user=lambda: "verified-user", engine_factory=builder)) as client:
        for _ in range(2):
            assert client.post("/v1/recommendations", json={"query": "Family drama"}).status_code == 200
    assert calls == ["initialized", "closed"]


@pytest.mark.parametrize("error,status", [
    (ConfigurationError, 503), (RepositoryUnavailable, 503), (ModelUnavailable, 503), (InvalidModelOutput, 502),
])
def test_upstream_errors_have_safe_http_responses(error, status):
    class FailingEngine:
        def recommend(self, request):
            raise error("upstream-sensitive-debug-text")
    app = FastAPI()
    app.include_router(recommendation_router(FailingEngine(), lambda: "verified-user"))
    response = TestClient(app).post("/v1/recommendations", json={"query": "Family drama"})
    assert response.status_code == status
    assert "upstream-sensitive-debug-text" not in response.text
