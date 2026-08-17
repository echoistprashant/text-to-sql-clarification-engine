from app.intent.models import QueryIntent
from app.schema.models import DatabaseSchema, SchemaRetrievalResult
from app.sql.joins import build_joins
from app.sql.models import (
    SQLAggregation,
    SQLColumn,
    SQLFilter,
    SQLOrder,
    SQLQuery,
)


def _find_table(
    schema: DatabaseSchema,
    table_name: str,
):
    for table in schema.tables:
        if table.name == table_name:
            return table

    raise ValueError(
        f"Table '{table_name}' does not exist in the schema."
    )


def _find_column(
    schema: DatabaseSchema,
    table_name: str,
    column_name: str,
):
    table = _find_table(
        schema,
        table_name,
    )

    for column in table.columns:
        if column.name == column_name:
            return column

    raise ValueError(
        f"Column '{table_name}.{column_name}' "
        "does not exist in the schema."
    )


def _find_display_column(
    schema: DatabaseSchema,
    table_name: str,
) -> str:
    table = _find_table(
        schema,
        table_name,
    )

    preferred_names = (
        "name",
        "title",
        "label",
        "description",
    )

    column_names = {
        column.name
        for column in table.columns
    }

    for preferred_name in preferred_names:
        if preferred_name in column_names:
            return preferred_name

    if table.primary_key:
        return table.primary_key[0]

    if not table.columns:
        raise ValueError(
            f"Table '{table_name}' has no columns."
        )

    return table.columns[0].name


def _split_qualified_column(
    value: str,
) -> tuple[str, str]:
    parts = value.split(".", 1)

    if len(parts) != 2:
        raise ValueError(
            f"Expected a qualified column name, got '{value}'."
        )

    return parts[0], parts[1]


def _build_filters(
    schema: DatabaseSchema,
    intent: QueryIntent,
    value_matches,
) -> list[SQLFilter]:
    filters: list[SQLFilter] = []

    for item in intent.filters:
        table_name, column_name = _split_qualified_column(
            item.column
        )

        _find_column(
            schema,
            table_name,
            column_name,
        )

        filters.append(
            SQLFilter(
                table=table_name,
                column=column_name,
                operator=item.operator,
                value=item.value,
            )
        )

    for match in value_matches:
        _find_column(
            schema,
            match.table_name,
            match.column_name,
        )

        filters.append(
            SQLFilter(
                table=match.table_name,
                column=match.column_name,
                operator="=",
                value=match.value,
            )
        )

    return filters


def plan_sql_query(
    schema: DatabaseSchema,
    intent: QueryIntent,
    schema_result: SchemaRetrievalResult,
) -> SQLQuery:
    if intent.entity is None:
        raise ValueError(
            "Query intent must contain an entity."
        )

    _find_table(
        schema,
        intent.entity,
    )

    if not schema_result.join_path:
        raise ValueError(
            "Schema retrieval result must contain a join path."
        )

    display_column = _find_display_column(
        schema,
        intent.entity,
    )

    select_columns = [
        SQLColumn(
            table=intent.entity,
            column=display_column,
        )
    ]

    aggregations: list[SQLAggregation] = []

    if intent.metric is not None:
        metric_table, metric_column = (
            _split_qualified_column(intent.metric)
        )

        _find_column(
            schema,
            metric_table,
            metric_column,
        )

        if intent.aggregation is None:
            raise ValueError(
                "A metric requires an aggregation."
            )

        aggregations.append(
            SQLAggregation(
                function=intent.aggregation.value.upper(),
                table=metric_table,
                column=metric_column,
                alias="metric_value",
            )
        )

    joins = build_joins(
        schema,
        schema_result.join_path,
    )

    filters = _build_filters(
        schema,
        intent,
        schema_result.value_matches,
    )

    group_by = [
        SQLColumn(
            table=intent.entity,
            column=display_column,
        )
    ]

    order_by: list[SQLOrder] = []

    if intent.sort_direction is not None:
        if not aggregations:
            raise ValueError(
                "Sorting an aggregated query requires a metric."
            )

        order_by.append(
            SQLOrder(
                expression="metric_value",
                direction=intent.sort_direction.value.upper(),
            )
        )

    return SQLQuery(
        select_columns=select_columns,
        joins=joins,
        filters=filters,
        aggregations=aggregations,
        group_by=group_by,
        order_by=order_by,
        limit=intent.limit,
    )