from app.intent.models import (
    Aggregation,
    QueryIntent,
    SortDirection,
)
from app.intent.workflow import create_clarification_state


def test_ambiguous_intent_creates_pending_clarification():
    intent = QueryIntent(
        entity="customers",
        sort_direction=SortDirection.DESC,
    )

    state = create_clarification_state(
        "Which customers bought the most laptops?",
        intent,
    )

    assert state.resolved is False
    assert len(state.ambiguities) == 1
    assert state.clarification is not None
    assert state.clarification.field == "metric"


def test_complete_intent_is_marked_resolved():
    intent = QueryIntent(
        entity="customers",
        metric="order_items.quantity",
        aggregation=Aggregation.SUM,
        sort_direction=SortDirection.DESC,
    )

    state = create_clarification_state(
        "Which customers bought the most laptops?",
        intent,
    )

    assert state.resolved is True
    assert state.ambiguities == []
    assert state.clarification is None