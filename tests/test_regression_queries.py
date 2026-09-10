from decimal import Decimal

import pytest
from app.db.schema_inspector import get_schema
from app.intent.models import Aggregation, IntentFilter, QueryIntent, SortDirection
from app.intent.workflow import create_clarification_state
from app.pipeline.analysis import AnalysisResult, refine_schema_with_intent
from app.pipeline.sql import _build_sql_result, execute_sql_analysis
from app.schema.retrieval import retrieve_schema


@pytest.fixture(scope="module")
def schema():
    return get_schema()


def _run_pipeline(schema, question: str, intent: QueryIntent):
    sr = retrieve_schema(schema, question)
    refined_sr = refine_schema_with_intent(schema, sr, intent)
    clarification = create_clarification_state(question, intent)
    analysis = AnalysisResult(
        question=question,
        schema=refined_sr,
        clarification=clarification,
    )
    sql_res = _build_sql_result(analysis, schema)
    return execute_sql_analysis(sql_res)


def test_q1_total_revenue(schema):
    """1. 'What is the total revenue?' -> Expected: 148000.00"""
    intent = QueryIntent(
        entity="orders",
        metric="orders.total_amount",
        aggregation=Aggregation.SUM,
    )
    result = _run_pipeline(schema, "What is the total revenue?", intent)
    assert "SELECT SUM(orders.total_amount)" in result.sql
    assert "GROUP BY" not in result.sql
    assert len(result.execution.rows) == 1
    assert result.execution.rows[0][0] == Decimal("148000.00")
    assert "148000.00" in result.answer


def test_q2_show_customers(schema):
    """2. 'Show customers' -> Expected: customer names"""
    intent = QueryIntent(entity="customers")
    result = _run_pipeline(schema, "Show customers", intent)
    assert "SELECT customers.name" in result.sql
    assert "FROM customers" in result.sql
    assert len(result.execution.rows) == 5
    names = {row[0] for row in result.execution.rows}
    assert "Rahul Sharma" in names
    assert "John Smith" in names


def test_q3_show_customers_from_india(schema):
    """3. 'Show customers from India' -> Expected: only matching customers"""
    intent = QueryIntent(
        entity="customers",
        filters=[
            IntentFilter(
                column="customers.country",
                operator="=",
                value="India",
            )
        ],
    )
    result = _run_pipeline(schema, "Show customers from India", intent)
    assert "SELECT customers.name" in result.sql
    assert "WHERE customers.country = :param_1" in result.sql
    assert result.parameters["param_1"] == "India"
    assert len(result.execution.rows) == 4
    names = {row[0] for row in result.execution.rows}
    assert "John Smith" not in names
    assert "Rahul Sharma" in names


def test_q4_revenue_by_customer(schema):
    """4. 'Show revenue by customer' -> Expected: one row per customer with aggregated revenue"""
    intent = QueryIntent(
        entity="orders",
        metric="orders.total_amount",
        aggregation=Aggregation.SUM,
        group_by="customers.name",
    )
    result = _run_pipeline(schema, "Show revenue by customer", intent)
    assert "SELECT customers.name" in result.sql
    assert "SUM(orders.total_amount)" in result.sql
    assert "FROM orders" in result.sql
    assert "JOIN customers" in result.sql
    assert "GROUP BY customers.name" in result.sql
    assert len(result.execution.rows) == 3
    revenue_by_name = {row[0]: row[1] for row in result.execution.rows}
    assert revenue_by_name["Rahul Sharma"] == Decimal("98000.00")
    assert revenue_by_name["Raman Sharma"] == Decimal("18000.00")
    assert revenue_by_name["Priya Singh"] == Decimal("32000.00")


def test_q5_revenue_by_product(schema):
    """5. 'Show revenue by product' -> Expected: one row per product"""
    intent = QueryIntent(
        entity="orders",
        metric="orders.total_amount",
        aggregation=Aggregation.SUM,
        group_by="products.name",
    )
    result = _run_pipeline(schema, "Show revenue by product", intent)
    assert "SELECT products.name" in result.sql
    assert "SUM(orders.total_amount)" in result.sql
    assert "GROUP BY products.name" in result.sql
    assert len(result.execution.rows) == 6


def test_q6_revenue_by_category(schema):
    """6. 'Show revenue by category' -> Expected: one row per category"""
    intent = QueryIntent(
        entity="orders",
        metric="orders.total_amount",
        aggregation=Aggregation.SUM,
        group_by="products.category",
    )
    result = _run_pipeline(schema, "Show revenue by category", intent)
    assert "SELECT products.category" in result.sql
    assert "SUM(orders.total_amount)" in result.sql
    assert "GROUP BY products.category" in result.sql
    assert len(result.execution.rows) == 3
    categories = {row[0] for row in result.execution.rows}
    assert categories == {"Electronics", "Accessories", "Furniture"}


def test_q7_revenue_by_customer_sorted_desc(schema):
    """7. 'Show revenue by customer sorted highest first' -> Expected: descending revenue"""
    intent = QueryIntent(
        entity="orders",
        metric="orders.total_amount",
        aggregation=Aggregation.SUM,
        group_by="customers.name",
        sort_direction=SortDirection.DESC,
    )
    result = _run_pipeline(
        schema, "Show revenue by customer sorted highest first", intent
    )
    assert "ORDER BY metric_value DESC" in result.sql
    amounts = [row[1] for row in result.execution.rows]
    assert amounts == sorted(amounts, reverse=True)


def test_q8_top_3_customers_by_revenue(schema):
    """8. 'Show top 3 customers by revenue' -> Expected: three customers ordered by revenue"""
    intent = QueryIntent(
        entity="orders",
        metric="orders.total_amount",
        aggregation=Aggregation.SUM,
        group_by="customers.name",
        sort_direction=SortDirection.DESC,
        limit=3,
    )
    result = _run_pipeline(schema, "Show top 3 customers by revenue", intent)
    assert "ORDER BY metric_value DESC" in result.sql
    assert "LIMIT 3" in result.sql
    assert len(result.execution.rows) == 3
    assert result.execution.rows[0][0] == "Rahul Sharma"


def test_q9_units_sold_by_product(schema):
    """9. 'How many units were sold by product?' -> Expected: SUM(order_items.quantity), grouped by product"""
    intent = QueryIntent(
        entity="order_items",
        metric="order_items.quantity",
        aggregation=Aggregation.SUM,
        group_by="products.name",
    )
    result = _run_pipeline(schema, "How many units were sold by product?", intent)
    assert "SELECT products.name" in result.sql
    assert "SUM(order_items.quantity)" in result.sql
    assert "GROUP BY products.name" in result.sql
    assert len(result.execution.rows) == 6


def test_q10_top_5_products_requires_clarification():
    """10. 'Show top 5 products' -> Expected: clarification if no ranking metric can be determined safely"""
    intent = QueryIntent(
        entity="products",
        sort_direction=SortDirection.DESC,
        limit=5,
    )
    state = create_clarification_state("Show top 5 products", intent)
    assert state.resolved is False
    assert state.clarification is not None
    assert state.clarification.field == "metric"
    assert len(state.clarification.options) > 0
