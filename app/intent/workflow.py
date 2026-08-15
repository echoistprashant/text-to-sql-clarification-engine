from app.intent.ambiguity import detect_ambiguities
from app.intent.clarification import build_clarification
from app.intent.models import QueryIntent
from app.intent.resolver import resolve_clarification
from app.intent.state import ClarificationState


def create_clarification_state(
    question: str,
    intent: QueryIntent,
) -> ClarificationState:
    ambiguities = detect_ambiguities(intent)

    if not ambiguities:
        return ClarificationState(
            question=question,
            intent=intent,
            ambiguities=[],
            clarification=None,
            resolved=True,
        )

    clarification = build_clarification(ambiguities[0])

    return ClarificationState(
        question=question,
        intent=intent,
        ambiguities=ambiguities,
        clarification=clarification,
        resolved=False,
    )


def answer_clarification(
    state: ClarificationState,
    answer: str,
) -> ClarificationState:
    if state.resolved:
        raise ValueError("The clarification is already resolved.")

    updated_intent = resolve_clarification(
        state,
        answer,
    )

    return create_clarification_state(
        state.question,
        updated_intent,
    )