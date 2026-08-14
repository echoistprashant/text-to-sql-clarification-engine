from app.schema.models import DatabaseSchema


def serialize_schema(schema: DatabaseSchema) -> str:
    sections: list[str] = []

    for table in sorted(schema.tables, key=lambda table: table.name):
        lines = [f"TABLE {table.name}", "COLUMNS:"]

        for column in table.columns:
            nullability = "NULL" if column.nullable else "NOT NULL"
            primary_key = (
                " [PRIMARY KEY]" if column.name in table.primary_key else ""
            )

            lines.append(
                f"- {column.name} {column.data_type} "
                f"{nullability}{primary_key}"
            )

        if table.foreign_keys:
            lines.append("RELATIONSHIPS:")

            for foreign_key in sorted(
                table.foreign_keys,
                key=lambda foreign_key: foreign_key.column,
            ):
                lines.append(
                    f"- {table.name}.{foreign_key.column} -> "
                    f"{foreign_key.references_table}."
                    f"{foreign_key.references_column}"
                )

        sections.append("\n".join(lines))

    return "\n\n".join(sections)