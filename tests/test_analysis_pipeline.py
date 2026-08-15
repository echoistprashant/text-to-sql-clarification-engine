from app.db.schema_inspector import get_schema
from app.pipeline.analysis import analyze_question


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


def test_analysis_pipeline_combines_schema_and_intent():
    schema = get_schema()

    result = analyze_question(
        "Which customers bought the most laptops?",
        schema,
        FakeLLMClient(),
        max_hops=3,
    )

    assert result.question == (
        "Which customers bought the most laptops?"
    )

    assert "customers" in result.schema.tables
    assert "products" in result.schema.tables

    assert any(
        match.table_name == "products"
        and match.value == "Laptop Pro 15"
        for match in result.schema.value_matches
    )

    assert result.clarification.resolved is False
    assert result.clarification.clarification is not None
    assert result.clarification.clarification.field == "metric"