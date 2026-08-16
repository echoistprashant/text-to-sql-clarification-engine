from app.sql.models import (
    SQLAggregation,
    SQLColumn,
    SQLFilter,
    SQLJoin,
    SQLOrder,
    SQLQuery,
)


def test_sql_query_represents_customer_ranking():
    query = SQLQuery(
        select_columns=[
            SQLColumn(
                table="customers",
                column="name",
            ),
        ],
        joins=[
            SQLJoin(
                left_table="customers",
                left_column="id",
                right_table="orders",
                right_column="customer_id",
            ),
            SQLJoin(
                left_table="orders",
                left_column="id",
                right_table="order_items",
                right_column="order_id",
            ),
            SQLJoin(
                left_table="order_items",
                left_column="product_id",
                right_table="products",
                right_column="id",
            ),
        ],
        filters=[
            SQLFilter(
                table="products",
                column="name",
                operator="LIKE",
                value="%Laptop%",
            ),
        ],
        aggregations=[
            SQLAggregation(
                function="SUM",
                table="order_items",
                column="quantity",
                alias="total_units",
            ),
        ],
        group_by=[
            SQLColumn(
                table="customers",
                column="name",
            ),
        ],
        order_by=[
            SQLOrder(
                expression="total_units",
                direction="DESC",
            ),
        ],
    )

    assert query.select_columns[0].table == "customers"
    assert query.select_columns[0].column == "name"

    assert len(query.joins) == 3

    assert query.filters[0].value == "%Laptop%"

    assert query.aggregations[0].function == "SUM"
    assert query.aggregations[0].column == "quantity"

    assert query.order_by[0].direction == "DESC"