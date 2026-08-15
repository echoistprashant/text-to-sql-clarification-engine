from sqlalchemy import text

from app.db.connection import engine
from app.schema.models import ColumnValueProfile


def profile_column_values(
    table_name: str,
    column_name: str,
    limit: int = 100,
) -> ColumnValueProfile:
    query = text(
        f"""
        SELECT DISTINCT "{column_name}"
        FROM "{table_name}"
        WHERE "{column_name}" IS NOT NULL
        ORDER BY "{column_name}"
        LIMIT :limit
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {"limit": limit},
        ).fetchall()

    values = [str(row[0]) for row in rows]

    return ColumnValueProfile(
        table_name=table_name,
        column_name=column_name,
        values=values,
    )