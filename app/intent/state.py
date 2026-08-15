from dataclasses import dataclass

from app.intent.ambiguity import Ambiguity
from app.intent.clarification import ClarificationRequest
from app.intent.models import QueryIntent


@dataclass(frozen=True)
class ClarificationState:
    question: str
    intent: QueryIntent
    ambiguities: list[Ambiguity]
    clarification: ClarificationRequest | None = None
    resolved: bool = False