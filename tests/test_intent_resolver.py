
from app.intent.ambiguity import detect_ambiguities
from app.intent.clarification import build_clarification
from app.intent.models import (
    QueryIntent,
    SortDirection,
)
from app.intent.state import ClarificationState


def make_state() -> ClarificationState:
    intent = QueryIntent(
        entity="customers",
        sort_direction=SortDirection.DESC,
    )

    ambiguities = detect_ambiguities(intent)
    clarification = build_clarification(ambiguities[0])

    return ClarificationState(
        question="Which customers bought the most laptops?",
        intent=intent,
        ambiguities=ambiguities,
        clarification=clarification,
        resolved=False,
    )