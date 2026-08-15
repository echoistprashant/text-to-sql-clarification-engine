from app.intent.models import (
    Aggregation,
    QueryIntent,
    SortDirection,
)
from app.intent.parser import parse_intent_response


def test_parse_intent_response():
    response = """
    {
        "entity": "customers",
        "filters": [],
        "metric": "order_items.quantity",
        "aggregation": "sum",
        "sort_direction": "desc",
        "limit": 5
    }
    """

    intent = parse_intent_response(response)

    assert intent == QueryIntent(
        entity="customers",
        metric="order_items.quantity",
        aggregation=Aggregation.SUM,
        sort_direction=SortDirection.DESC,
        limit=5,
    )