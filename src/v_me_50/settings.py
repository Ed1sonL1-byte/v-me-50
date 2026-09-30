"""Central, validated server configuration; secrets are never included in repr."""

import os
from collections.abc import Mapping
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, Field, SecretStr, ValidationError

from .errors import ConfigurationError


def required(env: Mapping[str, str], names: tuple[str, ...]) -> None:
    missing = [name for name in names if not env.get(name, "").strip()]
    if missing:
        raise ConfigurationError("Missing configuration: " + ", ".join(missing))


class RetrievalSettings(BaseModel):
    supabase_url: AnyHttpUrl
    supabase_publishable_key: SecretStr
    embedding_model: str = "BAAI/bge-m3"
    candidate_limit: int = Field(default=20, ge=1, le=100)
    timeout_seconds: float = Field(default=30, gt=0, le=120)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "RetrievalSettings":
        env = os.environ if env is None else env
        required(env, ("SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY"))
        try:
            return cls(
                supabase_url=env["SUPABASE_URL"],
                supabase_publishable_key=SecretStr(env["SUPABASE_PUBLISHABLE_KEY"]),
                embedding_model=env.get("EMBEDDING_MODEL", "BAAI/bge-m3"),
                candidate_limit=env.get("RAG_CANDIDATE_LIMIT", "20"),
                timeout_seconds=env.get("RETRIEVAL_TIMEOUT_SECONDS", "30"),
            )
        except ValidationError:
            raise ConfigurationError("Invalid Supabase or retrieval configuration.") from None


class LLMSettings(BaseModel):
    api_key: SecretStr
    model: str = Field(min_length=1)
    base_url: AnyHttpUrl | None = None
    timeout_seconds: float = Field(default=30, gt=0, le=120)
    max_retries: int = Field(default=2, ge=0, le=5)
    structured_output_method: Literal["json_schema", "function_calling"] = "json_schema"
    thinking_mode: Literal["enabled", "disabled"] | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "LLMSettings":
        env = os.environ if env is None else env
        required(env, ("OPENAI_API_KEY", "OPENAI_MODEL"))
        try:
            return cls(
                api_key=SecretStr(env["OPENAI_API_KEY"]), model=env["OPENAI_MODEL"].strip(),
                base_url=env.get("OPENAI_BASE_URL") or None,
                timeout_seconds=env.get("LLM_TIMEOUT_SECONDS", "30"),
                max_retries=env.get("LLM_MAX_RETRIES", "2"),
                structured_output_method=env.get("LLM_STRUCTURED_OUTPUT_METHOD", "json_schema"),
                thinking_mode=env.get("LLM_THINKING_MODE") or None,
            )
        except ValidationError:
            raise ConfigurationError("Invalid LLM configuration.") from None
