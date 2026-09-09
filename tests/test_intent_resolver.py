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


def test_resolve_units_purchased():
    from app.intent.resolver import resolve_clarification

    state = make_state()
    resolved = resolve_clarification(state, "Most units purchased")
    assert resolved.metric == "order_items.quantity"
    assert resolved.aggregation.value == "sum"


def test_resolve_orders():
    from app.intent.resolver import resolve_clarification

    state = make_state()
    resolved = resolve_clarification(state, "orders")
    assert resolved.metric == "orders.id"
    assert resolved.aggregation.value == "count"


def test_resolve_total_spending():
    from app.intent.resolver import resolve_clarification

    state = make_state()
    resolved = resolve_clarification(state, "total spending")
    assert resolved.metric == "orders.total_amount"
    assert resolved.aggregation.value == "sum"


def test_resolve_invalid_answer():
    import pytest

    from app.intent.resolver import resolve_clarification

    state = make_state()
    with pytest.raises(ValueError, match="Unsupported clarification answer"):
        resolve_clarification(state, "unknown metric")
