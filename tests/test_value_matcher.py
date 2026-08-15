from app.schema.models import ColumnValueProfile
from app.schema.value_matcher import (
    find_value_matches,
    normalize_text,
)


def test_normalize_text_singularizes_simple_plural():
    assert normalize_text("Laptops") == "laptop"


def test_value_matcher_finds_laptop_product():
    profile = ColumnValueProfile(
        table_name="products",
        column_name="name",
        values=[
            "Laptop Pro 15",
            "Wireless Mouse",
            "Mechanical Keyboard",
        ],
    )

    matches = find_value_matches(
        profile,
        "Which customers bought the most laptops?",
    )

    assert len(matches) == 1
    assert matches[0].table_name == "products"
    assert matches[0].column_name == "name"
    assert matches[0].value == "Laptop Pro 15"