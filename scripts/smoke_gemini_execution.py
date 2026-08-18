from dotenv import load_dotenv

from app.db.schema_inspector import get_schema
from app.llm.gemini import GeminiLLMClient
from app.pipeline.sql import analyze_for_sql
from app.sql.executor import execute_sql_query


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

    print()
    print("GENERATED SQL")
    print("=============")
    print(result.sql)

    print()
    print("PARAMETERS")
    print("==========")
    print(result.parameters)

    execution = execute_sql_query(
        result.query,
    )

    print()
    print("COLUMNS")
    print("=======")

    for column in execution.columns:
        print(f"- {column}")

    print()
    print("ROWS")
    print("====")

    for row in execution.rows:
        print(row)

    print()
    print("ROW COUNT")
    print("=========")
    print(len(execution.rows))


if __name__ == "__main__":
    main()