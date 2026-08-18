from app.sql.executor import SQLExecutionResult


def format_sql_result(
    result: SQLExecutionResult,
) -> str:
    if not result.rows:
        return "No results found."

    if len(result.columns) == 1:
        column = result.columns[0]

        if len(result.rows) == 1:
            return (
                f"{column}: "
                f"{result.rows[0][0]}"
            )

        lines = [
            f"{column}: {row[0]}"
            for row in result.rows
        ]

        return "\n".join(lines)

    if len(result.rows) == 1:
        row = result.rows[0]

        parts = [
            f"{column}: {value}"
            for column, value in zip(
                result.columns,
                row,
                strict=True,
            )
        ]

        return ", ".join(parts)

    lines = []

    for row in result.rows:
        parts = [
            f"{column}: {value}"
            for column, value in zip(
                result.columns,
                row,
                strict=True,
            )
        ]

        lines.append(", ".join(parts))

    return "\n".join(lines)