from app.sql.answer import format_sql_result
from app.sql.executor import SQLExecutionResult


def test_format_sql_result_returns_no_results_message():
    result = SQLExecutionResult(
        columns=["name"],
        rows=[],
    )

    assert (
        format_sql_result(result)
        == "No results found."
    )


def test_format_sql_result_formats_single_column():
    result = SQLExecutionResult(
        columns=["name"],
        rows=[
            ("Rahul Sharma",),
            ("Priya Patel",),
        ],
    )

    assert format_sql_result(result) == (
        "name: Rahul Sharma\n"
        "name: Priya Patel"
    )


def test_format_sql_result_formats_single_row():
    result = SQLExecutionResult(
        columns=[
            "name",
            "metric_value",
        ],
        rows=[
            ("Rahul Sharma", 1),
        ],
    )

    assert format_sql_result(result) == (
        "name: Rahul Sharma, "
        "metric_value: 1"
    )


def test_format_sql_result_formats_multiple_rows():
    result = SQLExecutionResult(
        columns=[
            "name",
            "metric_value",
        ],
        rows=[
            ("Rahul Sharma", 1),
            ("Priya Patel", 3),
        ],
    )

    assert format_sql_result(result) == (
        "name: Rahul Sharma, metric_value: 1\n"
        "name: Priya Patel, metric_value: 3"
    )