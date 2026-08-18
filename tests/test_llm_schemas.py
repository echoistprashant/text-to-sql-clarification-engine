from app.llm.schemas import INTENT_RESPONSE_SCHEMA


def test_intent_response_schema_contains_required_fields():
    required = (
        INTENT_RESPONSE_SCHEMA["required"]
    )

    assert "entity" in required
    assert "filters" in required
    assert "metric" in required
    assert "aggregation" in required
    assert "sort_direction" in required
    assert "limit" in required


def test_intent_response_schema_contains_filter_fields():
    filters = (
        INTENT_RESPONSE_SCHEMA["properties"][
            "filters"
        ]
    )

    filter_properties = (
        filters["items"]["properties"]
    )

    assert "column" in filter_properties
    assert "operator" in filter_properties
    assert "value" in filter_properties