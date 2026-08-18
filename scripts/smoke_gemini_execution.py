from dotenv import load_dotenv

from app.db.schema_inspector import get_schema
from app.llm.gemini import GeminiLLMClient
from app.pipeline.sql import (
    analyze_for_sql,
    execute_sql_analysis,
)


def main() -> None:
    load_dotenv()

    question = (
        "Which customers bought the most laptops?"
    )

    schema = get_schema()
    client = GeminiLLMClient()

    result = analyze_for_sql(
        question,
        schema,
        client,
        max_hops=3,
    )

    print("QUESTION")
    print("========")
    print(question)

    print()
    print("RESOLVED")
    print("========")
    print(
        result.analysis.clarification.resolved
    )

    if result.query is None:
        print()
        print("SQL QUERY WAS NOT BUILT.")
        return

    answer_result = execute_sql_analysis(
        result,
    )

    print()
    print("GENERATED SQL")
    print("=============")
    print(answer_result.sql)

    print()
    print("PARAMETERS")
    print("==========")
    print(answer_result.parameters)

    print()
    print("COLUMNS")
    print("=======")

    for column in answer_result.execution.columns:
        print(f"- {column}")

    print()
    print("ROWS")
    print("====")

    for row in answer_result.execution.rows:
        print(row)

    print()
    print("ROW COUNT")
    print("=========")
    print(
        len(answer_result.execution.rows)
    )

    print()
    print("FINAL ANSWER")
    print("============")
    print(answer_result.answer)


if __name__ == "__main__":
    main()