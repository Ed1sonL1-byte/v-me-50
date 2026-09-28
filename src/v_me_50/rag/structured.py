"""Common invocation boundary for structured LangChain stages."""

from typing import TypeVar

from langchain_core.runnables import Runnable
from langchain_core.exceptions import OutputParserException
from pydantic import BaseModel, ValidationError

from ..errors import InvalidModelOutput, ModelUnavailable


T = TypeVar("T", bound=BaseModel)


def invoke_structured(chain: Runnable, schema: type[T], values: dict) -> T:
    try:
        output = chain.invoke(values)
        return schema.model_validate(output)
    except (ValidationError, OutputParserException) as exc:
        raise InvalidModelOutput("The model response does not match the expected schema.") from exc
    except Exception as exc:
        raise ModelUnavailable("The language model call failed.") from exc
