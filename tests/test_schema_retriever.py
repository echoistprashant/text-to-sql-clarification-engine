from app.db.schema_inspector import get_schema
from app.schema.retriever import retrieve_tables


def test_retriever_finds_customers_table():
    schema = get_schema()

    tables = retrieve_tables(
        schema,
        "Show me all customers from India",
    )

    table_names = {table.name for table in tables}

    assert "customers" in table_names


def test_retriever_finds_products_table():
    schema = get_schema()

    tables = retrieve_tables(
        schema,
        "Show me products in the Electronics category",
    )

    table_names = {table.name for table in tables}

    assert "products" in table_names


def test_retriever_expands_related_tables():
    schema = get_schema()

    tables = retrieve_tables(
        schema,
        "Which customers bought the most laptops?",
        max_hops=3,
    )

    table_names = {table.name for table in tables}

    assert "customers" in table_names
    assert "orders" in table_names
    assert "order_items" in table_names
    assert "products" in table_names