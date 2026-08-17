from app.db.schema_inspector import get_schema
from app.intent.models import (
    Aggregation,
    QueryIntent,
    SortDirection,
)
from app.intent.state import ClarificationState
from app.pipeline.analysis import AnalysisResult
from app.pipeline.sql import _build_sql_result
from app.schema.retrieval import retrieve_schema


def test_build_sql_result_from_resolved_analysis():
    schema = get_schema()

    schema_result = retrieve_schema(
        schema,
        "Which customers bought the most laptops?",
        max_hops=3,
    )

    intent = QueryIntent(
        entity="customers",
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

    result = _build_sql_result(
        analysis,
        schema,
    )

    assert result.query is not None
    assert result.sql is not None
    assert result.parameters is not None

    assert "SELECT" in result.sql
    assert "FROM customers" in result.sql
    assert "JOIN orders" in result.sql
    assert "JOIN order_items" in result.sql
    assert "JOIN products" in result.sql
    assert "SUM(order_items.quantity)" in result.sql
    assert "WHERE products.name = :param_1" in result.sql
    assert "GROUP BY customers.name" in result.sql
    assert "ORDER BY metric_value DESC" in result.sql

    assert result.parameters == {
        "param_1": "Laptop Pro 15",
    }


def test_sql_result_contains_structured_query():
    schema = get_schema()

    schema_result = retrieve_schema(
        schema,
        "Which customers bought the most laptops?",
        max_hops=3,
    )

    intent = QueryIntent(
        entity="customers",
        metric="order_items.quantity",
        aggregation=Aggregation.SUM,
        sort_direction=SortDirection.DESC,
        limit=5,
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

    result = _build_sql_result(
        analysis,
        schema,
    )

    assert result.query is not None
    assert result.query.limit == 5
    assert result.query.aggregations[0].function == "SUM"
    assert result.query.order_by[0].direction == "DESC"

    assert result.parameters == {
        "param_1": "Laptop Pro 15",
    }