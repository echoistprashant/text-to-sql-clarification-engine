from app.db.schema_inspector import get_schema
from app.schema.serializer import serialize_schema


def test_schema_serialization_contains_tables():
    schema = get_schema()

    serialized = serialize_schema(schema)

    assert "TABLE customers" in serialized
    assert "TABLE products" in serialized
    assert "TABLE orders" in serialized
    assert "TABLE order_items" in serialized
    assert "TABLE payments" in serialized


def test_schema_serialization_contains_relationships():
    schema = get_schema()

    serialized = serialize_schema(schema)

    assert "orders.customer_id -> customers.id" in serialized
    assert "order_items.order_id -> orders.id" in serialized
    assert "order_items.product_id -> products.id" in serialized
    assert "payments.order_id -> orders.id" in serialized