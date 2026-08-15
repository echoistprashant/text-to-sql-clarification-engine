from app.schema.profiler import profile_column_values


def test_profile_products_names():
    profile = profile_column_values(
        "products",
        "name",
    )

    assert profile.table_name == "products"
    assert profile.column_name == "name"
    assert "Laptop Pro 15" in profile.values