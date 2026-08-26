from app.sql.models import CompiledSQL, SQLQuery


def compile_sql(query: SQLQuery) -> CompiledSQL:
    parts: list[str] = []
    parameters: dict[str, str] = {}

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
        raise ValueError(
            "SQL query must contain a SELECT expression."
        )

    parts.append(
        "SELECT " + ", ".join(select_items)
    )

    if query.select_columns:
        from_table = query.select_columns[0].table
    elif query.aggregations:
        from_table = query.aggregations[0].table
    else:
        raise ValueError(
            "SQL query must contain a FROM source."
        )

    parts.append(
        f"FROM {from_table}"
    )

    for join in query.joins:
        parts.append(
            f"{join.join_type} JOIN "
            f"{join.right_table} "
            f"ON {join.left_table}."
            f"{join.left_column} = "
            f"{join.right_table}."
            f"{join.right_column}"
        )

    if query.filters:
        filter_parts = []

        for index, item in enumerate(
            query.filters,
            start=1,
        ):
            parameter_name = f"param_{index}"

            filter_parts.append(
                f"{item.table}.{item.column} "
                f"{item.operator} "
                f":{parameter_name}"
            )

            parameters[parameter_name] = item.value

        parts.append(
            "WHERE " + " AND ".join(filter_parts)
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
            f"{item.expression} "
            f"{item.direction}"
            for item in query.order_by
        ]

        parts.append(
            "ORDER BY " + ", ".join(order_items)
        )

    if query.limit is not None:
        parts.append(
            f"LIMIT {query.limit}"
        )

    return CompiledSQL(
        sql="\n".join(parts) + ";",
        parameters=parameters,
    )


def generate_sql(query: SQLQuery) -> str:
    return compile_sql(query).sql