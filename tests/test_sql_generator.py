from app.sql.generator import generate_sql
from app.sql.models import (
    SQLAggregation,
    SQLColumn,
    SQLFilter,
    SQLJoin,
    SQLOrder,
    SQLQuery,
)


def test_generate_customer_laptop_ranking_sql():
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

    sql = generate_sql(query)

    assert "SELECT customers.name" in sql
    assert (
        "SUM(order_items.quantity) AS total_units"
        in sql
    )
    assert "FROM customers" in sql
    assert (
        "JOIN orders ON customers.id = orders.customer_id"
        in sql
    )
    assert (
        "JOIN order_items ON orders.id = order_items.order_id"
        in sql
    )
    assert (
        "JOIN products "
        "ON order_items.product_id = products.id"
        in sql
    )
    assert (
        "WHERE products.name LIKE '%Laptop%'"
        in sql
    )
    assert "GROUP BY customers.name" in sql
    assert "ORDER BY total_units DESC" in sql
    assert sql.endswith(";")


def test_generate_sql_requires_select_columns():
    query = SQLQuery()

    try:
        generate_sql(query)
    except ValueError as exc:
        assert str(exc) == (
            "SQL query must contain a SELECT expression."
        )
    else:
        raise AssertionError(
            "Expected ValueError for empty SELECT."
        )


def test_generate_sql_supports_limit():
    query = SQLQuery(
        select_columns=[
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
        limit=10,
    )

    sql = generate_sql(query)

    assert "LIMIT 10" in sql
