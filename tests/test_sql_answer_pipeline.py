from app.db.schema_inspector import get_schema
from app.intent.models import (
    Aggregation,
    QueryIntent,
    SortDirection,
)
from app.intent.state import ClarificationState
from app.pipeline.analysis import AnalysisResult
from app.pipeline.sql import (
    SQLAnalysisResult,
    _build_sql_result,
    execute_sql_analysis,
)
from app.schema.retrieval import retrieve_schema


def test_execute_sql_analysis_returns_formatted_answer():
    schema = get_schema()

    schema_result = retrieve_schema(
        schema,
        "Which customers bought the most laptops?",
        max_hops=3,
    )

    intent = QueryIntent(
        entity="customers",
        filters=[],
        metric="order_items.quantity",
        aggregation=Aggregation.SUM,
        sort_direction=SortDirection.DESC,
    )

    clarification = ClarificationState(
        question="Which customers bought the most laptops?",
        intent=intent,
        ambiguities=[],
        clarification=None,
        resolved=True,
    )

    analysis = AnalysisResult(
        question="Which customers bought the most laptops?",
        schema=schema_result,
        clarification=clarification,
    )

    sql_result = _build_sql_result(
        analysis,
        schema,
    )

    result = execute_sql_analysis(
        sql_result,
    )

    assert result.sql
    assert result.parameters == {
        "param_1": "Laptop Pro 15",
    }

    assert result.execution.columns == [
        "name",
        "metric_value",
    ]

    assert result.execution.rows == [
        ("Rahul Sharma", 1),
    ]

    assert result.answer == (
        "name: Rahul Sharma, metric_value: 1"
    )


def test_execute_sql_analysis_rejects_unresolved_result():
    schema = get_schema()

    schema_result = retrieve_schema(
        schema,
        "Which customers bought the most laptops?",
        max_hops=3,
    )

    intent = QueryIntent(
        entity="customers",
    )

    clarification = ClarificationState(
        question="Which customers bought the most laptops?",
        intent=intent,
        ambiguities=[],
        clarification=None,
        resolved=False,
    )

    analysis = AnalysisResult(
        question="Which customers bought the most laptops?",
        schema=schema_result,
        clarification=clarification,
    )

    result = SQLAnalysisResult(
        analysis=analysis,
    )

    try:
        execute_sql_analysis(result)
    except ValueError as exc:
        assert str(exc) == (
            "Cannot execute SQL from an unresolved analysis."
        )
    else:
        raise AssertionError(
            "Expected ValueError for unresolved SQL analysis."
        )