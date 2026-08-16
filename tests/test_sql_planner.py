from app.db.schema_inspector import get_schema
from app.intent.models import (
    Aggregation,
    QueryIntent,
    SortDirection,
)
from app.schema.retrieval import retrieve_schema
from app.sql.planner import plan_sql_query


def test_plan_sql_query_from_resolved_intent():
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

    query = plan_sql_query(
        schema,
        intent,
        schema_result,
    )

    assert query.select_columns[0].table == "customers"
    assert query.select_columns[0].column == "name"

    assert len(query.joins) == 3

    assert query.joins[0].left_table == "customers"
    assert query.joins[0].right_table == "orders"

    assert query.joins[1].left_table == "orders"
    assert query.joins[1].right_table == "order_items"

    assert query.joins[2].left_table == "order_items"
    assert query.joins[2].right_table == "products"

    assert len(query.aggregations) == 1

    aggregation = query.aggregations[0]

    assert aggregation.function == "SUM"
    assert aggregation.table == "order_items"
    assert aggregation.column == "quantity"
    assert aggregation.alias == "metric_value"

    assert query.group_by == [
        query.select_columns[0]
    ]

    assert query.order_by[0].expression == "metric_value"
    assert query.order_by[0].direction == "DESC"

    assert any(
        item.table == "products"
        and item.column == "name"
        and item.value == "Laptop Pro 15"
        for item in query.filters
    )

def test_planner_rejects_missing_entity():
    schema = get_schema()

    schema_result = retrieve_schema(
        schema,
        "Which customers bought the most laptops?",
        max_hops=3,
    )

    intent = QueryIntent(
        entity=None,
    )

    try:
        plan_sql_query(
            schema,
            intent,
            schema_result,
        )
    except ValueError as exc:
        assert str(exc) == (
            "Query intent must contain an entity."
        )
    else:
        raise AssertionError(
            "Expected ValueError for missing entity."
        )


def test_planner_rejects_unknown_metric_column():
    schema = get_schema()

    schema_result = retrieve_schema(
        schema,
        "Which customers bought the most laptops?",
        max_hops=3,
    )

    intent = QueryIntent(
        entity="customers",
        metric="order_items.does_not_exist",
        aggregation=Aggregation.SUM,
        sort_direction=SortDirection.DESC,
    )

    try:
        plan_sql_query(
            schema,
            intent,
            schema_result,
        )
    except ValueError as exc:
        assert (
            "does_not_exist"
            in str(exc)
        )
    else:
        raise AssertionError(
            "Expected ValueError for unknown metric."
        )    