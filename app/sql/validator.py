from app.schema.models import DatabaseSchema
from app.sql.models import SQLQuery

SUPPORTED_AGGREGATIONS = {
    "COUNT",
    "SUM",
    "AVG",
    "MIN",
    "MAX",
}

SUPPORTED_SORT_DIRECTIONS = {
    "ASC",
    "DESC",
}

SUPPORTED_JOIN_TYPES = {
    "INNER",
    "LEFT",
    "RIGHT",
    "FULL",
}

SUPPORTED_FILTER_OPERATORS = {
    "=",
    "!=",
    "<>",
    ">",
    ">=",
    "<",
    "<=",
    "LIKE",
    "NOT LIKE",
    "IN",
}


def _table_exists(
    schema: DatabaseSchema,
    table_name: str,
) -> bool:
    return any(
        table.name == table_name
        for table in schema.tables
    )


def _column_exists(
    schema: DatabaseSchema,
    table_name: str,
    column_name: str,
) -> bool:
    for table in schema.tables:
        if table.name != table_name:
            continue

        return any(
            column.name == column_name
            for column in table.columns
        )

    return False


def _validate_tables(
    schema: DatabaseSchema,
    query: SQLQuery,
) -> None:
    table_names = set()

    table_names.update(
        column.table
        for column in query.select_columns
    )

    table_names.update(
        join.left_table
        for join in query.joins
    )

    table_names.update(
        join.right_table
        for join in query.joins
    )

    table_names.update(
        item.table
        for item in query.filters
    )

    table_names.update(
        aggregation.table
        for aggregation in query.aggregations
    )

    table_names.update(
        column.table
        for column in query.group_by
    )

    for table_name in table_names:
        if not _table_exists(
            schema,
            table_name,
        ):
            raise ValueError(
                f"Table '{table_name}' "
                "does not exist in the schema."
            )


def _validate_columns(
    schema: DatabaseSchema,
    query: SQLQuery,
) -> None:
    for column in query.select_columns:
        if not _column_exists(
            schema,
            column.table,
            column.column,
        ):
            raise ValueError(
                f"Column '{column.table}.{column.column}' "
                "does not exist in the schema."
            )

    for item in query.filters:
        if not _column_exists(
            schema,
            item.table,
            item.column,
        ):
            raise ValueError(
                f"Column '{item.table}.{item.column}' "
                "does not exist in the schema."
            )

    for aggregation in query.aggregations:
        if not _column_exists(
            schema,
            aggregation.table,
            aggregation.column,
        ):
            raise ValueError(
                f"Column "
                f"'{aggregation.table}.{aggregation.column}' "
                "does not exist in the schema."
            )

    for column in query.group_by:
        if not _column_exists(
            schema,
            column.table,
            column.column,
        ):
            raise ValueError(
                f"Column '{column.table}.{column.column}' "
                "does not exist in the schema."
            )


def _validate_joins(
    schema: DatabaseSchema,
    query: SQLQuery,
) -> None:
    for join in query.joins:
        if join.join_type.upper() not in SUPPORTED_JOIN_TYPES:
            raise ValueError(
                f"Unsupported join type "
                f"'{join.join_type}'."
            )

        valid_relationship = False

        left_table = next(
            table
            for table in schema.tables
            if table.name == join.left_table
        )

        right_table = next(
            table
            for table in schema.tables
            if table.name == join.right_table
        )

        for foreign_key in left_table.foreign_keys:
            if (
                foreign_key.column == join.left_column
                and foreign_key.references_table
                == join.right_table
                and foreign_key.references_column
                == join.right_column
            ):
                valid_relationship = True
                break

        if not valid_relationship:
            for foreign_key in right_table.foreign_keys:
                if (
                    foreign_key.column == join.right_column
                    and foreign_key.references_table
                    == join.left_table
                    and foreign_key.references_column
                    == join.left_column
                ):
                    valid_relationship = True
                    break

        if not valid_relationship:
            raise ValueError(
                "Invalid foreign-key join: "
                f"{join.left_table}.{join.left_column} = "
                f"{join.right_table}.{join.right_column}"
            )


def _validate_aggregations(
    query: SQLQuery,
) -> None:
    for aggregation in query.aggregations:
        function = aggregation.function.upper()

        if function not in SUPPORTED_AGGREGATIONS:
            raise ValueError(
                f"Unsupported aggregation "
                f"'{aggregation.function}'."
            )


def _validate_filters(
    query: SQLQuery,
) -> None:
    for item in query.filters:
        operator = item.operator.upper()

        if operator not in SUPPORTED_FILTER_OPERATORS:
            raise ValueError(
                f"Unsupported filter operator "
                f"'{item.operator}'."
            )


def _validate_ordering(
    query: SQLQuery,
) -> None:
    for item in query.order_by:
        direction = item.direction.upper()

        if direction not in SUPPORTED_SORT_DIRECTIONS:
            raise ValueError(
                f"Unsupported sort direction "
                f"'{item.direction}'."
            )


def _validate_limit(
    query: SQLQuery,
) -> None:
    if query.limit is None:
        return

    if query.limit <= 0:
        raise ValueError(
            "LIMIT must be greater than zero."
        )


def validate_sql_query(
    schema: DatabaseSchema,
    query: SQLQuery,
) -> None:
    if not query.select_columns:
        raise ValueError(
            "SQL query must contain at least one "
            "SELECT column."
        )

    _validate_tables(
        schema,
        query,
    )

    _validate_columns(
        schema,
        query,
    )

    _validate_joins(
        schema,
        query,
    )

    _validate_aggregations(
        query,
    )

    _validate_filters(
        query,
    )

    _validate_ordering(
        query,
    )

    _validate_limit(
        query,
    )