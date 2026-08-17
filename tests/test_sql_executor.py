from app.sql.executor import execute_sql_query
from app.sql.models import (
    SQLColumn,
    SQLFilter,
    SQLQuery,
)


def test_execute_sql_query_returns_rows():
    query = SQLQuery(
        select_columns=[
            SQLColumn(
                table="customers",
                column="name",
            ),
        ],
        filters=[
            SQLFilter(
                table="customers",
                column="country",
                operator="=",
                value="India",
            ),
        ],
    )

    result = execute_sql_query(query)

    assert "name" in result.columns
    assert isinstance(result.rows, list)


def test_execute_sql_query_supports_parameterized_values():
    query = SQLQuery(
        select_columns=[
            SQLColumn(
                table="customers",
                column="name",
            ),
        ],
        filters=[
            SQLFilter(
                table="customers",
                column="name",
                operator="=",
                value="O'Reilly",
            ),
        ],
    )

    result = execute_sql_query(query)

    assert isinstance(result.rows, list)