from app.db.schema_inspector import get_schema
from app.schema.models import ForeignKeySchema


def test_schema_contains_expected_tables():
    schema = get_schema()

    table_names = {table.name for table in schema.tables}

    assert "customers" in table_names
    assert "products" in table_names
    assert "orders" in table_names
    assert "order_items" in table_names
    assert "payments" in table_names


def test_orders_has_customer_foreign_key():
    schema = get_schema()

    orders = next(table for table in schema.tables if table.name == "orders")

    assert ForeignKeySchema(
        column="customer_id",
        references_table="customers",
        references_column="id",
    ) in orders.foreign_keys