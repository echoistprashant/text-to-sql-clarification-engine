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


FORBIDDEN_REQUEST_KEYWORDS = {
    "ALTER",
    "CREATE",
    "DELETE",
    "DROP",
    "GRANT",
    "INSERT",
    "MERGE",
    "REVOKE",
    "TRUNCATE",
    "UPDATE",
}


def validate_read_only_request(
    question: str,
) -> None:
    normalized = re.sub(
        r"\s+",
        " ",
        question.strip(),
    ).upper()

    if not normalized:
        return

    for keyword in FORBIDDEN_REQUEST_KEYWORDS:
        if re.search(
            rf"\b{keyword}\b",
            normalized,
        ):
            raise ValueError(
                "Only read-only database questions are supported."
            )


def validate_read_only_sql(
    sql: str,
) -> None:
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