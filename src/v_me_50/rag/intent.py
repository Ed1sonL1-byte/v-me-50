"""Natural-language requests to typed movie preferences."""

from ..models import Intent
from ..ports import StructuredChatModel
from .prompts import INTENT_PROMPT
from .structured import invoke_structured


class IntentParser:
    def __init__(self, llm: StructuredChatModel):
        self.chain = INTENT_PROMPT | llm.with_structured_output(Intent)

    def parse(self, request: str) -> Intent:
        return invoke_structured(self.chain, Intent, {"request": request})
