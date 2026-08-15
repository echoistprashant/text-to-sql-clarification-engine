from app.intent.ambiguity import detect_ambiguities
from app.intent.models import (
    Aggregation,
    QueryIntent,
    SortDirection,
)


def test_ranking_without_metric_is_ambiguous():
    intent = QueryIntent(
        entity="customers",
        sort_direction=SortDirection.DESC,
    )

    ambiguities = detect_ambiguities(intent)

    assert len(ambiguities) == 1
    assert ambiguities[0].field == "metric"


def test_complete_ranking_intent_is_not_ambiguous():
    intent = QueryIntent(
        entity="customers",
        metric="order_items.quantity",
        aggregation=Aggregation.SUM,
        sort_direction=SortDirection.DESC,
    )

    ambiguities = detect_ambiguities(intent)

    assert ambiguities == []


def test_aggregation_without_metric_is_ambiguous():
    intent = QueryIntent(
        entity="customers",
        aggregation=Aggregation.SUM,
    )

    ambiguities = detect_ambiguities(intent)

    assert len(ambiguities) == 1
    assert ambiguities[0].field == "metric"