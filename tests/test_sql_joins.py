import pytest

from app.db.schema_inspector import get_schema
from app.sql.joins import build_joins, resolve_join


def test_resolve_customer_orders_join():
    schema = get_schema()

    join = resolve_join(
        schema,
        "customers",
        "orders",
    )

    assert join.left_table == "customers"
    assert join.left_column == "id"
    assert join.right_table == "orders"
    assert join.right_column == "customer_id"


def test_resolve_reverse_direction_join():
    schema = get_schema()

    join = resolve_join(
        schema,
        "orders",
        "customers",
    )

    assert join.left_table == "orders"
    assert join.left_column == "customer_id"
    assert join.right_table == "customers"
    assert join.right_column == "id"


def test_build_laptop_join_path():
    schema = get_schema()

    joins = build_joins(
        schema,
        [
            "customers",
            "orders",
            "order_items",
            "products",
        ],
    )

    assert len(joins) == 3

    assert joins[0].left_table == "customers"
    assert joins[0].right_table == "orders"

    assert joins[1].left_table == "orders"
    assert joins[1].right_table == "order_items"

    assert joins[2].left_table == "order_items"
    assert joins[2].right_table == "products"


def test_single_table_path_has_no_joins():
    schema = get_schema()

    joins = build_joins(
        schema,
        ["customers"],
    )

    assert joins == []


def test_invalid_join_is_rejected():
    schema = get_schema()

    with pytest.raises(ValueError, match="No foreign-key relationship"):
        resolve_join(
            schema,
            "customers",
            "products",
        )