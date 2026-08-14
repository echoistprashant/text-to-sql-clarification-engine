from sqlalchemy import inspect

from app.db.connection import engine
from app.schema.models import (
    ColumnSchema,
    DatabaseSchema,
    ForeignKeySchema,
    TableSchema,
)


def get_schema() -> DatabaseSchema:
    inspector = inspect(engine)

    tables = []

    for table_name in inspector.get_table_names():
        columns = [
            ColumnSchema(
                name=column["name"],
                data_type=str(column["type"]),
                nullable=column["nullable"],
            )
            for column in inspector.get_columns(table_name)
        ]

        primary_key = inspector.get_pk_constraint(table_name)[
            "constrained_columns"
        ]

        foreign_keys = [
            ForeignKeySchema(
                column=foreign_key["constrained_columns"][0],
                references_table=foreign_key["referred_table"],
                references_column=foreign_key["referred_columns"][0],
            )
            for foreign_key in inspector.get_foreign_keys(table_name)
        ]

        tables.append(
            TableSchema(
                name=table_name,
                columns=columns,
                primary_key=primary_key,
                foreign_keys=foreign_keys,
            )
        )

    return DatabaseSchema(tables=tables)