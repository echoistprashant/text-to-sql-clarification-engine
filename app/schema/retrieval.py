from app.schema.graph import build_schema_graph
from app.schema.join_path import select_join_path
from app.schema.models import DatabaseSchema, SchemaRetrievalResult
from app.schema.profiler import profile_column_values
from app.schema.ranker import rank_tables
from app.schema.retriever import retrieve_tables
from app.schema.value_matcher import find_value_matches

TEXT_COLUMNS = {
    "CHAR",
    "VARCHAR",
    "TEXT",
}


def retrieve_schema(
    schema: DatabaseSchema,
    question: str,
    max_hops: int = 2,
) -> SchemaRetrievalResult:
    tables = retrieve_tables(
        schema,
        question,
        max_hops=max_hops,
    )

    value_matches = []

    for table in tables:
        for column in table.columns:
            data_type = column.data_type.upper()

            if not any(
                data_type.startswith(text_type)
                for text_type in TEXT_COLUMNS
            ):
                continue

            profile = profile_column_values(
                table.name,
                column.name,
            )

            value_matches.extend(
                find_value_matches(
                    profile,
                    question,
                )
            )

    table_names = [table.name for table in tables]

    for match in value_matches:
        if match.table_name not in table_names:
            table_names.append(match.table_name)

    ranked_tables = rank_tables(
        schema,
        question,
        table_names,
        value_matches,
    )

    graph = build_schema_graph(schema)

    required_tables = {
        ranked_table.table_name
        for ranked_table in ranked_tables
        if ranked_table.score >= 5
    }

    join_path = select_join_path(
        graph,
        required_tables,
    )

    return SchemaRetrievalResult(
        tables=table_names,
        value_matches=value_matches,
        ranked_tables=ranked_tables,
        join_path=join_path,
    )