import pytest

from app.sql.safety import validate_read_only_sql


def test_select_is_allowed():
    validate_read_only_sql(
        "SELECT name FROM customers"
    )


def test_select_with_whitespace_is_allowed():
    validate_read_only_sql(
        """
        SELECT
            name
        FROM
            customers
        """
    )


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO customers (name) VALUES ('Alice')",
        "UPDATE customers SET name = 'Alice'",
        "DELETE FROM customers",
        "DROP TABLE customers",
        "ALTER TABLE customers ADD COLUMN age INT",
        "CREATE TABLE test (id INT)",
        "TRUNCATE TABLE customers",
        "GRANT SELECT ON customers TO user1",
        "REVOKE SELECT ON customers FROM user1",
        "MERGE INTO customers USING other_table",
    ],
)
def test_mutating_sql_is_rejected(sql):
    with pytest.raises(
        ValueError,
        match="Only SELECT statements|Forbidden SQL operation",
    ):
        validate_read_only_sql(sql)


def test_empty_sql_is_rejected():
    with pytest.raises(
        ValueError,
        match="SQL query cannot be empty",
    ):
        validate_read_only_sql("")


def test_multiple_statements_are_rejected():
    with pytest.raises(
        ValueError,
        match="Only one SQL statement",
    ):
        validate_read_only_sql(
            "SELECT name FROM customers; "
            "DELETE FROM customers"
        )


def test_non_select_statement_is_rejected():
    with pytest.raises(
        ValueError,
        match="Only SELECT statements",
    ):
        validate_read_only_sql(
            "SHOW TABLES"
        )