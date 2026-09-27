from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from v_me_50.api import recommendation_router
from v_me_50.models import RecommendationResponse


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
