"""OpenAI-compatible LangChain model connection and HTTP client ownership."""

import httpx
from langchain_openai import ChatOpenAI

from ..settings import LLMSettings


class OpenAIChatModel:
    def __init__(self, settings: LLMSettings):
        self.structured_output_method = settings.structured_output_method
        self.http_client = httpx.Client(timeout=settings.timeout_seconds)
        try:
            self.model = ChatOpenAI(
                model=settings.model, api_key=settings.api_key.get_secret_value(),
                base_url=str(settings.base_url) if settings.base_url else None,
                temperature=0, timeout=settings.timeout_seconds, max_retries=settings.max_retries,
                extra_body={"thinking": {"type": settings.thinking_mode}} if settings.thinking_mode else None,
                http_client=self.http_client,
            )
        except Exception:
            self.http_client.close()
            raise

    def with_structured_output(self, schema):
        return self.model.with_structured_output(schema, method=self.structured_output_method)

    def close(self) -> None:
        self.http_client.close()
