from app.schema.graph import shortest_path


def select_join_path(
    graph: dict[str, set[str]],
    required_tables: set[str],
) -> list[str]:
    if not required_tables:
        return []

    if len(required_tables) == 1:
        return [next(iter(required_tables))]

    tables = sorted(required_tables)

    best_path: list[str] | None = None

    start = tables[0]

    for target in tables[1:]:
        path = shortest_path(
            graph,
            start,
            target,
        )

        if path is None:
            continue

        if best_path is None or len(path) < len(best_path):
            best_path = path

    return best_path or []