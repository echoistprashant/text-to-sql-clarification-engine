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
from app.sql.executor import execute_sql_query


def test_end_to_end_sql_generation_and_execution():
    schema = get_schema()

    question = (
        "Which customers bought the most laptops?"
    )

    schema_result = retrieve_schema(
        schema,
        question,
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
        question=question,
        intent=intent,
        ambiguities=[],
        clarification=None,
        resolved=True,
    )

    analysis = AnalysisResult(
        question=question,
        schema=schema_result,
        clarification=clarification,
    )

    sql_result = _build_sql_result(
        analysis,
        schema,
    )

    assert sql_result.query is not None
    assert sql_result.sql is not None
    assert sql_result.parameters is not None

    assert "SELECT" in sql_result.sql
    assert "FROM customers" in sql_result.sql
    assert "JOIN orders" in sql_result.sql
    assert "JOIN order_items" in sql_result.sql
    assert "JOIN products" in sql_result.sql
    assert "SUM(order_items.quantity)" in sql_result.sql
    assert (
        "WHERE products.name = :param_1"
        in sql_result.sql
    )
    assert "GROUP BY customers.name" in sql_result.sql
    assert "ORDER BY metric_value DESC" in sql_result.sql
    assert "LIMIT 5" in sql_result.sql

    assert sql_result.parameters == {
        "param_1": "Laptop Pro 15",
    }

    execution_result = execute_sql_query(
        sql_result.query,
    )

    assert execution_result.columns
    assert execution_result.rows

    assert execution_result.columns[0] == "name"
    assert "metric_value" in execution_result.columns

    assert len(execution_result.rows) <= 5