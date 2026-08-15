from collections import deque

from app.schema.models import DatabaseSchema


def build_schema_graph(
    schema: DatabaseSchema,
) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {
        table.name: set()
        for table in schema.tables
    }

    for table in schema.tables:
        for foreign_key in table.foreign_keys:
            graph[table.name].add(
                foreign_key.references_table
            )
            graph[foreign_key.references_table].add(
                table.name
            )

    return graph


def expand_tables(
    graph: dict[str, set[str]],
    seed_tables: set[str],
    max_hops: int = 1,
) -> set[str]:
    visited = set(seed_tables)
    queue = deque(
        (table, 0)
        for table in seed_tables
    )

    while queue:
        current_table, hops = queue.popleft()

        if hops >= max_hops:
            continue

        for neighbor in graph.get(
            current_table,
            set(),
        ):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(
                    (neighbor, hops + 1)
                )

    return visited


def shortest_distance(
    graph: dict[str, set[str]],
    start: str,
    target: str,
) -> int | None:
    if start == target:
        return 0

    visited = {start}
    queue = deque([(start, 0)])

    while queue:
        current_table, distance = queue.popleft()

        for neighbor in graph.get(
            current_table,
            set(),
        ):
            if neighbor == target:
                return distance + 1

            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(
                    (neighbor, distance + 1)
                )

    return None

def shortest_path(
    graph: dict[str, set[str]],
    start: str,
    target: str,
) -> list[str] | None:
    if start == target:
        return [start]

    visited = {start}
    queue = deque([(start, [start])])

    while queue:
        current_table, path = queue.popleft()

        for neighbor in graph.get(current_table, set()):
            if neighbor in visited:
                continue

            new_path = [*path, neighbor]

            if neighbor == target:
                return new_path

            visited.add(neighbor)
            queue.append((neighbor, new_path))

    return None