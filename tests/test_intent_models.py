from app.intent.models import (
    Aggregation,
    IntentFilter,
    QueryIntent,
    SortDirection,
)


def test_query_intent_can_represent_simple_entity():
    intent = QueryIntent(
        entity="customers",
    )

    assert intent.entity == "customers"
    assert intent.filters == []
    assert intent.metric is None
    assert intent.aggregation is None


def test_query_intent_can_represent_filters():
    intent = QueryIntent(
        entity="customers",
        filters=[
            IntentFilter(
                column="country",
                operator="=",
                value="India",
            )
        ],
    )

    assert intent.entity == "customers"
    assert len(intent.filters) == 1
    assert intent.filters[0].column == "country"
    assert intent.filters[0].value == "India"


def test_query_intent_can_represent_ranking():
    intent = QueryIntent(
        entity="customers",
        metric="order_items.quantity",
        aggregation=Aggregation.SUM,
        sort_direction=SortDirection.DESC,
        limit=5,
    )

    assert intent.metric == "order_items.quantity"
    assert intent.aggregation == Aggregation.SUM
    assert intent.sort_direction == SortDirection.DESC
    assert intent.limit == 5