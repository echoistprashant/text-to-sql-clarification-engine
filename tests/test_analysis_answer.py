from app.db.schema_inspector import get_schema
from app.pipeline.analysis import (
    analyze_question,
    answer_analysis,
)


class FakeLLMClient:
    def generate(self, prompt: str) -> str:
        return """
        {
            "entity": "customers",
            "filters": [],
            "metric": null,
            "aggregation": null,
            "sort_direction": "desc",
            "limit": null
        }
        """


def test_analysis_can_be_resolved_by_user_answer():
    schema = get_schema()
    llm_client = FakeLLMClient()

    result = analyze_question(
        "Which customers bought the most laptops?",
        schema,
        llm_client,
        max_hops=3,
    )

    assert result.clarification.resolved is False
    assert result.clarification.clarification is not None

    resolved = answer_analysis(
        result,
        "Most units purchased",
    )

    assert resolved.question == (
        "Which customers bought the most laptops?"
    )

    assert resolved.clarification.resolved is True
    assert resolved.clarification.ambiguities == []
    assert resolved.clarification.clarification is None

    assert resolved.clarification.intent.entity == "customers"
    assert (
        resolved.clarification.intent.metric
        == "order_items.quantity"
    )
    assert (
        resolved.clarification.intent.aggregation.value
        == "sum"
    )
    assert (
        resolved.clarification.intent.sort_direction.value
        == "desc"
    )

    assert "customers" in resolved.schema.tables
    assert "products" in resolved.schema.tables

    assert any(
        match.table_name == "products"
        and match.value == "Laptop Pro 15"
        for match in resolved.schema.value_matches
    )

def test_answer_analysis_rejects_answer_after_resolution():
    schema = get_schema()
    llm_client = FakeLLMClient()

    result = analyze_question(
        "Which customers bought the most laptops?",
        schema,
        llm_client,
        max_hops=3,
    )

    resolved = answer_analysis(
        result,
        "Most orders",
    )

    assert resolved.clarification.resolved is True

    try:
        answer_analysis(
            resolved,
            "Most units purchased",
        )
    except ValueError as exc:
        assert str(exc) == "The clarification is already resolved."
    else:
        raise AssertionError(
            "Expected ValueError for an already resolved analysis."
        )    