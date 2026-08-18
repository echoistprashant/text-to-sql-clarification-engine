import pytest

from app.intent.models import (
    Aggregation,
    IntentFilter,
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


def test_parse_intent_response_parses_filters():
    response = """
    {
        "entity": "customers",
        "filters": [
            {
                "column": "customers.country",
                "operator": "=",
                "value": "India"
            }
        ],
        "metric": null,
        "aggregation": null,
        "sort_direction": null,
        "limit": null
    }
    """

    intent = parse_intent_response(response)

    assert intent.filters == [
        IntentFilter(
            column="customers.country",
            operator="=",
            value="India",
        )
    ]


def test_parse_intent_response_rejects_invalid_json():
    with pytest.raises(
        ValueError,
        match="LLM response is not valid JSON",
    ):
        parse_intent_response(
            '{"entity": "customers"'
        )


def test_parse_intent_response_requires_object():
    with pytest.raises(
        TypeError,
        match="must be a JSON object",
    ):
        parse_intent_response(
            '["customers"]'
        )


def test_parse_intent_response_rejects_invalid_aggregation():
    response = """
    {
        "entity": "customers",
        "filters": [],
        "metric": "order_items.quantity",
        "aggregation": "banana",
        "sort_direction": null,
        "limit": null
    }
    """

    with pytest.raises(
        ValueError,
        match="Unsupported aggregation",
    ):
        parse_intent_response(response)


def test_parse_intent_response_rejects_invalid_sort_direction():
    response = """
    {
        "entity": "customers",
        "filters": [],
        "metric": null,
        "aggregation": null,
        "sort_direction": "sideways",
        "limit": null
    }
    """

    with pytest.raises(
        ValueError,
        match="Unsupported sort direction",
    ):
        parse_intent_response(response)


def test_parse_intent_response_rejects_invalid_filters():
    response = """
    {
        "entity": "customers",
        "filters": {},
        "metric": null,
        "aggregation": null,
        "sort_direction": null,
        "limit": null
    }
    """

    with pytest.raises(
        TypeError,
        match="'filters' must be a list",
    ):
        parse_intent_response(response)


def test_parse_intent_response_rejects_incomplete_filter():
    response = """
    {
        "entity": "customers",
        "filters": [
            {
                "column": "customers.country",
                "operator": "="
            }
        ],
        "metric": null,
        "aggregation": null,
        "sort_direction": null,
        "limit": null
    }
    """

    with pytest.raises(
        ValueError,
        match="missing required field 'value'",
    ):
        parse_intent_response(response)


def test_parse_intent_response_rejects_invalid_limit():
    response = """
    {
        "entity": "customers",
        "filters": [],
        "metric": null,
        "aggregation": null,
        "sort_direction": null,
        "limit": "5"
    }
    """

    with pytest.raises(
        ValueError,
        match="'limit' must be an integer",
    ):
        parse_intent_response(response)


def test_parse_intent_response_rejects_non_positive_limit():
    response = """
    {
        "entity": "customers",
        "filters": [],
        "metric": null,
        "aggregation": null,
        "sort_direction": null,
        "limit": 0
    }
    """

    with pytest.raises(
        ValueError,
        match="'limit' must be greater than zero",
    ):
        parse_intent_response(response)


def test_parse_intent_response_normalizes_eq_operator():
    response = """
    {
        "entity": "customers",
        "filters": [
            {
                "column": "products.name",
                "operator": "eq",
                "value": "Laptop Pro 15"
            }
        ],
        "metric": "order_items.quantity",
        "aggregation": "sum",
        "sort_direction": "desc",
        "limit": null
    }
    """

    intent = parse_intent_response(response)

    assert intent.filters == [
        IntentFilter(
            column="products.name",
            operator="=",
            value="Laptop Pro 15",
        )
    ]


def test_parse_intent_response_normalizes_comparison_operators():
    operators = {
        "neq": "!=",
        "gt": ">",
        "gte": ">=",
        "lt": "<",
        "lte": "<=",
    }

    for source, expected in operators.items():
        response = f"""
        {{
            "entity": "customers",
            "filters": [
                {{
                    "column": "customers.id",
                    "operator": "{source}",
                    "value": "5"
                }}
            ],
            "metric": null,
            "aggregation": null,
            "sort_direction": null,
            "limit": null
        }}
        """

        intent = parse_intent_response(response)

        assert intent.filters[0].operator == expected


def test_parse_intent_response_normalizes_contains_to_like():
    response = """
    {
        "entity": "products",
        "filters": [
            {
                "column": "products.name",
                "operator": "contains",
                "value": "Laptop"
            }
        ],
        "metric": null,
        "aggregation": null,
        "sort_direction": null,
        "limit": null
    }
    """

    intent = parse_intent_response(response)

    assert intent.filters[0].operator == "LIKE"


def test_parse_intent_response_rejects_unsupported_operator():
    response = """
    {
        "entity": "customers",
        "filters": [
            {
                "column": "customers.country",
                "operator": "approximately",
                "value": "India"
            }
        ],
        "metric": null,
        "aggregation": null,
        "sort_direction": null,
        "limit": null
    }
    """

    with pytest.raises(
        ValueError,
        match="Unsupported filter operator",
    ):
        parse_intent_response(response)


def test_parse_intent_response_rejects_non_string_operator():
    response = """
    {
        "entity": "customers",
        "filters": [
            {
                "column": "customers.country",
                "operator": 123,
                "value": "India"
            }
        ],
        "metric": null,
        "aggregation": null,
        "sort_direction": null,
        "limit": null
    }
    """

    with pytest.raises(
        TypeError,
        match="Filter operator must be a string",
    ):
        parse_intent_response(response)

