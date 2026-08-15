import pytest

from app.intent.models import QueryIntent, SortDirection
from app.intent.workflow import (
    answer_clarification,
    create_clarification_state,
)


def test_unknown_clarification_answer_is_rejected():
    intent = QueryIntent(
        entity="customers",
        sort_direction=SortDirection.DESC,
    )

    state = create_clarification_state(
        "Which customers bought the most laptops?",
        intent,
    )

    with pytest.raises(ValueError):
        answer_clarification(
            state,
            "I don't know",
        )


def test_non_ranking_intent_does_not_require_clarification():
    intent = QueryIntent(
        entity="customers",
    )

    state = create_clarification_state(
        "Show me all customers.",
        intent,
    )

    assert state.resolved is True
    assert state.clarification is None
    assert state.ambiguities == []


def test_clarification_preserves_original_filters():
    from app.intent.models import IntentFilter

    intent = QueryIntent(
        entity="customers",
        filters=[
            IntentFilter(
                column="country",
                operator="=",
                value="India",
            )
        ],
        sort_direction=SortDirection.DESC,
    )

    state = create_clarification_state(
        "Which Indian customers bought the most laptops?",
        intent,
    )

    resolved = answer_clarification(
        state,
        "Most units purchased",
    )

    assert resolved.intent.filters == [
        IntentFilter(
            column="country",
            operator="=",
            value="India",
        )
    ]