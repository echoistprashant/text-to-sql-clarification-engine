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

    # 1. Check if any pair has a path covering all required tables
    best_path: list[str] | None = None
    for start in tables:
        for target in tables:
            if start == target:
                continue
            path = shortest_path(graph, start, target)
            if (
                path
                and required_tables.issubset(set(path))
                and (best_path is None or len(path) < len(best_path))
            ):
                best_path = path

    if best_path:
        return best_path

    # 2. If no single direct path covers all, choose the root with shortest total distance
    best_combined: list[str] | None = None
    for root in sorted(graph.keys()):
        paths = [shortest_path(graph, root, t) for t in tables]
        if any(p is None for p in paths):
            continue
        combined = [root]
        for p in sorted(paths, key=lambda x: len(x) if x else 0):
            if p:
                for node in p:
                    if node not in combined:
                        combined.append(node)
        if best_combined is None or len(combined) < len(best_combined):
            best_combined = combined

    return best_combined or []
