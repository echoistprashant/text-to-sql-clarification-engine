from app.schema.models import (
    DatabaseSchema,
    SchemaRetrievalResult,
)
from app.schema.serializer import serialize_schema


def build_llm_schema_context(
    schema: DatabaseSchema,
    schema_result: SchemaRetrievalResult,
) -> str:
    relevant_table_names = set(
        schema_result.tables
    )

    relevant_table_names.update(
        schema_result.join_path
    )

    relevant_tables = [
        table
        for table in schema.tables
        if table.name in relevant_table_names
    ]

    relevant_schema = DatabaseSchema(
        tables=sorted(
            relevant_tables,
            key=lambda table: table.name,
        )
    )

    sections = [
        "RELEVANT DATABASE SCHEMA:",
        serialize_schema(relevant_schema),
    ]

    if schema_result.join_path:
        sections.extend(
            [
                "",
                "RELEVANT JOIN PATH:",
                " -> ".join(schema_result.join_path),
            ]
        )

    if schema_result.value_matches:
        sections.extend(
            [
                "",
                "RELEVANT DATABASE VALUES:",
            ]
        )

        for match in schema_result.value_matches:
            sections.append(
                f"- {match.table_name}."
                f"{match.column_name} = "
                f'"{match.value}"'
            )

    return "\n".join(sections)