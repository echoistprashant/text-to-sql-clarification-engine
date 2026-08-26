import pytest

from app.db.schema_inspector import get_schema
from app.intent.models import (
    Aggregation,
    IntentFilter,
    QueryIntent,
    SortDirection,
)
from app.schema.retrieval import retrieve_schema
from app.sql.models import (
    SQLAggregation,
    SQLFilter,
)
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


@pytest.mark.parametrize(
    "aggregation",
    [
        Aggregation.COUNT,
        Aggregation.SUM,
        Aggregation.AVG,
        Aggregation.MIN,
        Aggregation.MAX,
    ],
)
def test_planner_supports_all_aggregations(
    aggregation,
):
    schema = get_schema()

    schema_result = retrieve_schema(
        schema,
        "Which customers bought the most laptops?",
        max_hops=3,
    )

    intent = QueryIntent(
        entity="customers",
        metric="order_items.quantity",
        aggregation=aggregation,
        sort_direction=SortDirection.DESC,
    )

    query = plan_sql_query(
        schema,
        intent,
        schema_result,
    )

    assert len(query.aggregations) == 1
    assert (
        query.aggregations[0].function
        == aggregation.value.upper()
    )


def test_planner_converts_intent_filters():
    schema = get_schema()

    schema_result = retrieve_schema(
        schema,
        "Show customers from India",
        max_hops=2,
    )

    intent = QueryIntent(
        entity="customers",
        filters=[
            IntentFilter(
                column="customers.country",
                operator="=",
                value="India",
            ),
        ],
    )

    query = plan_sql_query(
        schema,
        intent,
        schema_result,
    )

    assert any(
        item.table == "customers"
        and item.column == "country"
        and item.operator == "="
        and item.value == "India"
        for item in query.filters
    )


def test_planner_deduplicates_intent_and_value_match_filters():
    schema = get_schema()

    schema_result = retrieve_schema(
        schema,
        "Which customers bought the most laptops?",
        max_hops=3,
    )

    intent = QueryIntent(
        entity="customers",
        filters=[
            IntentFilter(
                column="products.name",
                operator="=",
                value="Laptop Pro 15",
            ),
        ],
        metric="order_items.quantity",
        aggregation=Aggregation.SUM,
        sort_direction=SortDirection.DESC,
    )

    query = plan_sql_query(
        schema,
        intent,
        schema_result,
    )

    matching_filters = [
        item
        for item in query.filters
        if item.table == "products"
        and item.column == "name"
        and item.operator == "="
        and item.value == "Laptop Pro 15"
    ]

    assert matching_filters == [
        SQLFilter(
            table="products",
            column="name",
            operator="=",
            value="Laptop Pro 15",
        ),
    ]


def test_planner_preserves_distinct_filters():
    schema = get_schema()

    schema_result = retrieve_schema(
        schema,
        "Which customers bought the most laptops?",
        max_hops=3,
    )

    intent = QueryIntent(
        entity="customers",
        filters=[
            IntentFilter(
                column="products.name",
                operator="=",
                value="Laptop Pro 15",
            ),
            IntentFilter(
                column="customers.country",
                operator="=",
                value="India",
            ),
        ],
        metric="order_items.quantity",
        aggregation=Aggregation.SUM,
        sort_direction=SortDirection.DESC,
    )

    query = plan_sql_query(
        schema,
        intent,
        schema_result,
    )

    assert any(
        item.table == "products"
        and item.column == "name"
        and item.operator == "="
        and item.value == "Laptop Pro 15"
        for item in query.filters
    )

    assert any(
        item.table == "customers"
        and item.column == "country"
        and item.operator == "="
        and item.value == "India"
        for item in query.filters
    )


def test_planner_supports_ascending_sort():
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
        sort_direction=SortDirection.ASC,
    )

    query = plan_sql_query(
        schema,
        intent,
        schema_result,
    )

    assert query.order_by[0].direction == "ASC"
    assert query.order_by[0].expression == "metric_value"


def test_planner_preserves_limit():
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
        limit=10,
    )

    query = plan_sql_query(
        schema,
        intent,
        schema_result,
    )

    assert query.limit == 10


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

    with pytest.raises(
        ValueError,
        match="Query intent must contain an entity.",
    ):
        plan_sql_query(
            schema,
            intent,
            schema_result,
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

    with pytest.raises(
        ValueError,
        match="does_not_exist",
    ):
        plan_sql_query(
            schema,
            intent,
            schema_result,
        )


def test_planner_rejects_metric_without_aggregation():
    schema = get_schema()

    schema_result = retrieve_schema(
        schema,
        "Which customers bought the most laptops?",
        max_hops=3,
    )

    intent = QueryIntent(
        entity="customers",
        metric="order_items.quantity",
    )

    with pytest.raises(
        ValueError,
        match="A metric requires an aggregation.",
    ):
        plan_sql_query(
            schema,
            intent,
            schema_result,
        )


def test_planner_rejects_sort_without_metric():
    schema = get_schema()

    schema_result = retrieve_schema(
        schema,
        "Which customers bought the most laptops?",
        max_hops=3,
    )

    intent = QueryIntent(
        entity="customers",
        sort_direction=SortDirection.DESC,
    )

    with pytest.raises(
        ValueError,
        match="Sorting an aggregated query requires a metric.",
    ):
        plan_sql_query(
            schema,
            intent,
            schema_result,
        )


def test_planner_rejects_missing_join_path():
    schema = get_schema()

    schema_result = retrieve_schema(
        schema,
        "Which customers bought the most laptops?",
        max_hops=3,
    )

    schema_result = type(schema_result)(
        tables=schema_result.tables,
        value_matches=schema_result.value_matches,
        ranked_tables=schema_result.ranked_tables,
        join_path=[],
    )

    intent = QueryIntent(
        entity="customers",
    )

    with pytest.raises(
        ValueError,
        match="must contain a join path",
    ):
        plan_sql_query(
            schema,
            intent,
            schema_result,
        )

def test_planner_does_not_group_standalone_aggregation():
    schema = get_schema()

    schema_result = retrieve_schema(
        schema,
        "How many laptops were sold?",
        max_hops=3,
    )

    intent = QueryIntent(
        entity="order_items",
        filters=[
            IntentFilter(
                column="products.name",
                operator="LIKE",
                value="%Laptop%",
            ),
        ],
        metric="order_items.quantity",
        aggregation=Aggregation.SUM,
    )

    query = plan_sql_query(
        schema,
        intent,
        schema_result,
    )

    assert query.select_columns == []

    assert len(query.aggregations) == 1

    assert query.aggregations[0] == SQLAggregation(
        function="SUM",
        table="order_items",
        column="quantity",
        alias="metric_value",
    )

    assert query.group_by == []