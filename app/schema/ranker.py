from app.schema.graph import build_schema_graph, shortest_distance
from app.schema.models import (
    DatabaseSchema,
    RankedTable,
    ValueMatch,
)


def rank_tables(
    schema: DatabaseSchema,
    question: str,
    candidate_tables: list[str],
    value_matches: list[ValueMatch],
) -> list[RankedTable]:
    question_terms = set(
        question.lower().split()
    )

    graph = build_schema_graph(schema)

    value_match_tables = {
        match.table_name
        for match in value_matches
    }

    direct_tables = {
        table.name
        for table in schema.tables
        if table.name.lower() in question_terms
    }

    evidence_tables = (
        value_match_tables | direct_tables
    )

    ranked = []

    for table in schema.tables:
        if table.name not in candidate_tables:
            continue

        score = 0

        if table.name in direct_tables:
            score += 5

        for column in table.columns:
            if column.name.lower() in question_terms:
                score += 3

        if table.name in value_match_tables:
            score += 7

        distances = []

        for evidence_table in evidence_tables:
            distance = shortest_distance(
                graph,
                evidence_table,
                table.name,
            )

            if distance is not None:
                distances.append(distance)

        if distances:
            nearest_distance = min(distances)

            if nearest_distance == 1:
                score += 2
            elif nearest_distance == 2:
                score += 1

        ranked.append(
            RankedTable(
                table_name=table.name,
                score=score,
            )
        )

    ranked.sort(
        key=lambda item: (-item.score, item.table_name)
    )

    return ranked