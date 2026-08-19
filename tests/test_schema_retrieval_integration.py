from app.db.schema_inspector import get_schema
from app.schema.retrieval import retrieve_schema


def test_retrieve_schema_finds_laptop_join_path():
    schema = get_schema()

    result = retrieve_schema(
        schema,
        "Which customers bought the most laptops?",
        max_hops=3,
    )

    assert any(
        match.table_name == "products"
        and match.column_name == "name"
        and match.value == "Laptop Pro 15"
        for match in result.value_matches
    )

    assert result.ranked_tables[0].table_name == "products"

    assert result.join_path == [
        "customers",
        "orders",
        "order_items",
        "products",
    ]

def test_retrieve_schema_finds_product_from_value_only_question():
    schema = get_schema()

    result = retrieve_schema(
        schema,
        "How many laptops were sold?",
        max_hops=3,
    )

    assert "products" in result.tables

    assert any(
        match.table_name == "products"
        and match.column_name == "name"
        and match.value == "Laptop Pro 15"
        for match in result.value_matches
    )

    assert result.ranked_tables[0].table_name == "products"

    assert result.join_path == [
        "products",
    ]    