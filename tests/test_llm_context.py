from app.llm.context import build_llm_schema_context
from app.schema.models import (
    DatabaseSchema,
    SchemaRetrievalResult,
    TableSchema,
    ValueMatch,
)


def test_build_llm_schema_context_contains_relevant_schema():
    schema = DatabaseSchema(
        tables=[
            TableSchema(
                name="customers",
                columns=[],
                primary_key=[],
                foreign_keys=[],
            ),
            TableSchema(
                name="products",
                columns=[],
                primary_key=[],
                foreign_keys=[],
            ),
            TableSchema(
                name="payments",
                columns=[],
                primary_key=[],
                foreign_keys=[],
            ),
        ]
    )

    schema_result = SchemaRetrievalResult(
        tables=[
            "customers",
            "products",
        ],
        value_matches=[],
        ranked_tables=[],
        join_path=[
            "customers",
            "products",
        ],
    )

    context = build_llm_schema_context(
        schema,
        schema_result,
    )

    assert "RELEVANT DATABASE SCHEMA:" in context
    assert "TABLE customers" in context
    assert "TABLE products" in context
    assert "TABLE payments" not in context


def test_build_llm_schema_context_contains_join_path():
    schema = DatabaseSchema(
        tables=[]
    )

    schema_result = SchemaRetrievalResult(
        tables=[],
        value_matches=[],
        ranked_tables=[],
        join_path=[
            "customers",
            "orders",
            "order_items",
            "products",
        ],
    )

    context = build_llm_schema_context(
        schema,
        schema_result,
    )

    assert (
        "customers -> orders -> "
        "order_items -> products"
    ) in context


def test_build_llm_schema_context_contains_value_matches():
    schema = DatabaseSchema(
        tables=[]
    )

    schema_result = SchemaRetrievalResult(
        tables=[],
        value_matches=[
            ValueMatch(
                table_name="products",
                column_name="name",
                value="Laptop Pro 15",
            )
        ],
        ranked_tables=[],
        join_path=[],
    )

    context = build_llm_schema_context(
        schema,
        schema_result,
    )

    assert "RELEVANT DATABASE VALUES:" in context
    assert (
        'products.name = "Laptop Pro 15"'
        in context
    )