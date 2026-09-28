"""Reference-aware semantic queries, separate from hard and soft constraints."""

from ..models import Intent, Movie, ReferenceQuery
from ..ports import StructuredChatModel
from .prompts import REFERENCE_QUERY_PROMPT
from .structured import invoke_structured


class ReferenceQueryBuilder:
    def __init__(self, llm: StructuredChatModel):
        self.chain = REFERENCE_QUERY_PROMPT | llm.with_structured_output(ReferenceQuery)

    def build(self, request: str, intent: Intent, reference: Movie | None) -> str:
        if reference is None:
            return intent.semantic_query
        record = reference.model_dump(exclude={"similarity"})
        record["plot"] = reference.plot[:6000]
        query = invoke_structured(self.chain, ReferenceQuery, {
            "request": request, "intent": intent.model_dump_json(), "reference": record,
        })
        return query.semantic_query
