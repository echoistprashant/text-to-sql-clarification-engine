from itertools import pairwise

from app.schema.models import DatabaseSchema
from app.sql.models import SQLJoin


def _get_table(
    schema: DatabaseSchema,
    table_name: str,
):
    for table in schema.tables:
        if table.name == table_name:
            return table

    raise ValueError(
        f"Table '{table_name}' does not exist in the schema."
    )


def resolve_join(
    schema: DatabaseSchema,
    left_table_name: str,
    right_table_name: str,
) -> SQLJoin:
    left_table = _get_table(
        schema,
        left_table_name,
    )

    right_table = _get_table(
        schema,
        right_table_name,
    )

    for foreign_key in left_table.foreign_keys:
        if foreign_key.references_table == right_table_name:
            return SQLJoin(
                left_table=left_table_name,
                left_column=foreign_key.column,
                right_table=right_table_name,
                right_column=foreign_key.references_column,
            )

    for foreign_key in right_table.foreign_keys:
        if foreign_key.references_table == left_table_name:
            return SQLJoin(
                left_table=left_table_name,
                left_column=foreign_key.references_column,
                right_table=right_table_name,
                right_column=foreign_key.column,
            )

    raise ValueError(
        "No foreign-key relationship exists between "
        f"'{left_table_name}' and '{right_table_name}'."
    )


def build_joins(
    schema: DatabaseSchema,
    join_path: list[str],
) -> list[SQLJoin]:
    if len(join_path) < 2:
        return []

    return [
        resolve_join(
            schema,
            left_table,
            right_table,
        )
        for left_table, right_table in pairwise(join_path)
    ]