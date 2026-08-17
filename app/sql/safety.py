import re

FORBIDDEN_SQL_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "GRANT",
    "REVOKE",
    "MERGE",
}


def validate_read_only_sql(sql: str) -> None:
    normalized = re.sub(
        r"\s+",
        " ",
        sql.strip(),
    ).upper()

    if not normalized:
        raise ValueError(
            "SQL query cannot be empty."
        )

    statements = [
        statement.strip()
        for statement in normalized.split(";")
        if statement.strip()
    ]

    if len(statements) > 1:
        raise ValueError(
            "Only one SQL statement is allowed."
        )

    statement = statements[0]

    if not statement.startswith("SELECT"):
        raise ValueError(
            "Only SELECT statements are allowed."
        )

    for keyword in FORBIDDEN_SQL_KEYWORDS:
        if re.search(
            rf"\b{keyword}\b",
            statement,
        ):
            raise ValueError(
                f"Forbidden SQL operation: {keyword}."
            )