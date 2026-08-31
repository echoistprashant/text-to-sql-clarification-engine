from app.intent.models import QueryIntent
from app.schema.graph import (
    build_schema_graph,
    shortest_path,
)
from app.schema.models import (
    DatabaseSchema,
    SchemaRetrievalResult,
)
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
    seen: set[tuple[str, str, str, str]] = set()

    concrete_value_keys = {
        (
            match.table_name,
            match.column_name,
        )
        for match in value_matches
    }

    for item in intent.filters:
        table_name, column_name = _split_qualified_column(
            item.column
        )

        _find_column(
            schema,
            table_name,
            column_name,
        )

        # A concrete schema value match is more precise than
        # a broad textual filter on the same column.
        if (
            (table_name, column_name) in concrete_value_keys
            and item.operator.upper() in {"LIKE", "NOT LIKE"}
        ):
            continue

        filter_key = (
            table_name,
            column_name,
            item.operator,
            item.value,
        )

        if filter_key in seen:
            continue

        seen.add(filter_key)

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

        filter_key = (
            match.table_name,
            match.column_name,
            "=",
            match.value,
        )

        if filter_key in seen:
            continue

        seen.add(filter_key)

        filters.append(
            SQLFilter(
                table=match.table_name,
                column=match.column_name,
                operator="=",
                value=match.value,
            )
        )

    return filters

def _collect_required_tables(
    intent: QueryIntent,
    schema_result: SchemaRetrievalResult,
) -> set[str]:
    required_tables = {
        intent.entity,
    }

    for item in intent.filters:
        table_name, _ = _split_qualified_column(
            item.column
        )
        required_tables.add(table_name)

    if intent.metric is not None:
        metric_table, _ = _split_qualified_column(
            intent.metric
        )
        required_tables.add(metric_table)

    for match in schema_result.value_matches:
        required_tables.add(
            match.table_name
        )

    return required_tables


def _build_join_path(
    schema: DatabaseSchema,
    intent: QueryIntent,
    schema_result: SchemaRetrievalResult,
) -> list[str]:
    if not schema_result.join_path:
        raise ValueError(
            "Schema retrieval result must contain a join path."
        )

    required_tables = _collect_required_tables(
        intent,
        schema_result,
    )

    existing_path = list(
        schema_result.join_path
    )

    if required_tables.issubset(
        set(existing_path)
    ):
        if intent.entity in existing_path:
            entity_index = existing_path.index(
                intent.entity
            )

            if entity_index == 0:
                return existing_path

        graph = build_schema_graph(
            schema
        )

        rebuilt_path = [intent.entity]

        for required_table in sorted(
            required_tables
        ):
            if required_table == intent.entity:
                continue

            path = shortest_path(
                graph,
                intent.entity,
                required_table,
            )

            if path is None:
                raise ValueError(
                    "No join path exists between "
                    "the tables required by the query."
                )

            for table_name in path[1:]:
                if table_name not in rebuilt_path:
                    rebuilt_path.append(
                        table_name
                    )

        return rebuilt_path

    graph = build_schema_graph(
        schema
    )

    combined_path = [intent.entity]

    for required_table in sorted(
        required_tables
    ):
        if required_table == intent.entity:
            continue

        path = shortest_path(
            graph,
            intent.entity,
            required_table,
        )

        if path is None:
            raise ValueError(
                "No join path exists between "
                f"'{intent.entity}' and "
                f"'{required_table}'."
            )

        for table_name in path[1:]:
            if table_name not in combined_path:
                combined_path.append(
                    table_name
                )

    return combined_path


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

    join_path = _build_join_path(
        schema,
        intent,
        schema_result,
    )

    aggregations: list[SQLAggregation] = []

    if intent.metric is not None:
        metric_table, metric_column = (
            _split_qualified_column(
                intent.metric
            )
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

    is_standalone_aggregation = (
        bool(aggregations)
        and intent.sort_direction is None
        and intent.entity == "order_items"
    )

    if is_standalone_aggregation:
        select_columns: list[SQLColumn] = []
        group_by: list[SQLColumn] = []
    else:
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

        group_by = [
            SQLColumn(
                table=intent.entity,
                column=display_column,
            )
        ]

    joins = build_joins(
        schema,
        join_path,
    )

    filters = _build_filters(
        schema,
        intent,
        schema_result.value_matches,
    )

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