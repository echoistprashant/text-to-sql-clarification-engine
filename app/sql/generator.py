from app.sql.models import SQLQuery


def generate_sql(query: SQLQuery) -> str:
    parts: list[str] = []

    select_parts = [
        f"{column.table}.{column.column}"
        + (
            f" AS {column.alias}"
            if column.alias
            else ""
        )
        for column in query.select_columns
    ]

    aggregation_parts = [
        f"{aggregation.function}("
        f"{aggregation.table}.{aggregation.column}"
        f")"
        + (
            f" AS {aggregation.alias}"
            if aggregation.alias
            else ""
        )
        for aggregation in query.aggregations
    ]

    select_items = [
        *select_parts,
        *aggregation_parts,
    ]

    if not select_items:
        raise ValueError("SQL query must contain a SELECT expression.")

    parts.append(
        "SELECT " + ", ".join(select_items)
    )

    if not query.select_columns:
        raise ValueError(
            "SQL query must contain at least one selected column."
        )

    from_table = query.select_columns[0].table
    parts.append(f"FROM {from_table}")

    for join in query.joins:
        parts.append(
            f"{join.join_type} JOIN {join.right_table} "
            f"ON {join.left_table}.{join.left_column} = "
            f"{join.right_table}.{join.right_column}"
        )

    if query.filters:
        filters = [
            (
                f"{item.table}.{item.column} "
                f"{item.operator} "
                f"'{item.value}'"
            )
            for item in query.filters
        ]

        parts.append(
            "WHERE " + " AND ".join(filters)
        )

    if query.group_by:
        group_columns = [
            f"{column.table}.{column.column}"
            for column in query.group_by
        ]

        parts.append(
            "GROUP BY " + ", ".join(group_columns)
        )

    if query.order_by:
        order_items = [
            f"{item.expression} {item.direction}"
            for item in query.order_by
        ]

        parts.append(
            "ORDER BY " + ", ".join(order_items)
        )

    if query.limit is not None:
        parts.append(f"LIMIT {query.limit}")

    return "\n".join(parts) + ";"