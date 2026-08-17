import pytest

from app.db.schema_inspector import get_schema
from app.sql.models import (
    SQLAggregation,
    SQLColumn,
    SQLJoin,
    SQLOrder,
    SQLQuery,
)
from app.sql.validator import validate_sql_query


def test_valid_query_passes_validation():
    schema = get_schema()

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
        ],
    )

    validate_sql_query(
        schema,
        query,
    )


def test_unknown_table_is_rejected():
    schema = get_schema()

    query = SQLQuery(
        select_columns=[
            SQLColumn(
                table="does_not_exist",
                column="name",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="does_not_exist",
    ):
        validate_sql_query(
            schema,
            query,
        )


def test_unknown_column_is_rejected():
    schema = get_schema()

    query = SQLQuery(
        select_columns=[
            SQLColumn(
                table="customers",
                column="does_not_exist",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="does_not_exist",
    ):
        validate_sql_query(
            schema,
            query,
        )


def test_invalid_join_is_rejected():
    schema = get_schema()

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
                right_table="products",
                right_column="id",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="Invalid foreign-key join",
    ):
        validate_sql_query(
            schema,
            query,
        )


def test_invalid_aggregation_is_rejected():
    schema = get_schema()

    query = SQLQuery(
        select_columns=[
            SQLColumn(
                table="customers",
                column="name",
            ),
        ],
        aggregations=[
            SQLAggregation(
                function="MEDIAN",
                table="orders",
                column="id",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="Unsupported aggregation",
    ):
        validate_sql_query(
            schema,
            query,
        )


def test_invalid_sort_direction_is_rejected():
    schema = get_schema()

    query = SQLQuery(
        select_columns=[
            SQLColumn(
                table="customers",
                column="name",
            ),
        ],
        order_by=[
            SQLOrder(
                expression="name",
                direction="SIDEWAYS",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="Unsupported sort direction",
    ):
        validate_sql_query(
            schema,
            query,
        )


def test_invalid_limit_is_rejected():
    schema = get_schema()

    query = SQLQuery(
        select_columns=[
            SQLColumn(
                table="customers",
                column="name",
            ),
        ],
        limit=0,
    )

    with pytest.raises(
        ValueError,
        match="LIMIT must be greater than zero",
    ):
        validate_sql_query(
            schema,
            query,
        )