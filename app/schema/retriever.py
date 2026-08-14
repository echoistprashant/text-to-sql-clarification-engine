from app.schema.graph import build_schema_graph, expand_tables
from app.schema.models import DatabaseSchema, TableSchema


def find_seed_tables(
    schema: DatabaseSchema,
    question: str,
) -> set[str]:
    question_terms = set(question.lower().split())

    seed_tables = set()

    for table in schema.tables:
        table_terms = {table.name.lower()}

        for column in table.columns:
            table_terms.add(column.name.lower())

        if question_terms & table_terms:
            seed_tables.add(table.name)

    return seed_tables


def score_table_relevance(
    table: TableSchema,
    question: str,
) -> int:
    question_terms = set(question.lower().split())

    score = 0

    if table.name.lower() in question_terms:
        score += 3

    for column in table.columns:
        if column.name.lower() in question_terms:
            score += 1

    return score


def retrieve_tables(
    schema: DatabaseSchema,
    question: str,
    max_hops: int = 1,
) -> list[TableSchema]:
    seed_tables = find_seed_tables(schema, question)

    if not seed_tables:
        return []

    graph = build_schema_graph(schema)

    candidate_tables = expand_tables(
        graph,
        seed_tables,
        max_hops=max_hops,
    )

    scored_tables = [
        (
            table,
            score_table_relevance(table, question),
        )
        for table in schema.tables
        if table.name in candidate_tables
    ]

    scored_tables.sort(
        key=lambda item: (-item[1], item[0].name)
    )

    return [table for table, _ in scored_tables]