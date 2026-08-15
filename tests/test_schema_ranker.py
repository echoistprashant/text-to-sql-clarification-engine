from app.db.schema_inspector import get_schema
from app.schema.models import ValueMatch
from app.schema.ranker import rank_tables


def test_products_ranks_high_for_laptop_question():
    schema = get_schema()

    value_matches = [
        ValueMatch(
            table_name="products",
            column_name="name",
            value="Laptop Pro 15",
        )
    ]

    ranked = rank_tables(
        schema,
        "Which customers bought the most laptops?",
        [
            "customers",
            "orders",
            "order_items",
            "products",
            "payments",
        ],
        value_matches,
    )

    assert ranked[0].table_name == "products"
    assert ranked[0].score == 7