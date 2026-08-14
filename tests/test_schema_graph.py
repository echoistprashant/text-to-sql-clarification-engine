from app.db.schema_inspector import get_schema
from app.schema.graph import build_schema_graph, expand_tables


def test_schema_graph_contains_expected_relationships():
    schema = get_schema()

    graph = build_schema_graph(schema)

    assert "orders" in graph["customers"]
    assert "customers" in graph["orders"]

    assert "order_items" in graph["orders"]
    assert "orders" in graph["order_items"]

    assert "products" in graph["order_items"]
    assert "order_items" in graph["products"]

    assert "payments" in graph["orders"]
    assert "orders" in graph["payments"]


def test_schema_graph_can_expand_related_tables():
    schema = get_schema()

    graph = build_schema_graph(schema)

    expanded = expand_tables(
        graph,
        {"customers"},
        max_hops=2,
    )

    assert "customers" in expanded
    assert "orders" in expanded
    assert "order_items" in expanded