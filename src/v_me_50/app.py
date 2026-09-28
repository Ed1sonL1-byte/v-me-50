"""ASGI entry point: uvicorn v_me_50.app:create_app --factory."""

from .api.application import create_app

__all__ = ["create_app"]
