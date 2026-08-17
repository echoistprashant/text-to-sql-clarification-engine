from dataclasses import dataclass

from sqlalchemy import text

from app.db.connection import engine
from app.sql.generator import compile_sql
from app.sql.models import SQLQuery
from app.sql.safety import validate_read_only_sql


@dataclass(frozen=True)
class SQLExecutionResult:
    columns: list[str]
    rows: list[tuple]


def execute_sql_query(
    query: SQLQuery,
) -> SQLExecutionResult:
    compiled = compile_sql(query)

    validate_read_only_sql(
        compiled.sql,
    )

    with engine.connect() as connection:
        result = connection.execute(
            text(compiled.sql),
            compiled.parameters,
        )

        rows = result.fetchall()

        return SQLExecutionResult(
            columns=list(result.keys()),
            rows=[
                tuple(row)
                for row in rows
            ],
        )