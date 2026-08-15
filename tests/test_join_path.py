from app.db.schema_inspector import get_schema
from app.schema.graph import build_schema_graph
from app.schema.join_path import select_join_path


def test_select_join_path_connects_customers_and_products():
    schema = get_schema()
    graph = build_schema_graph(schema)

    path = select_join_path(
        graph,
        {"customers", "products"},
    )

    assert path == [
        "customers",
        "orders",
        "order_items",
        "products",
    ]