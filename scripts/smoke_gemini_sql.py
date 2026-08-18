from dotenv import load_dotenv

from app.db.schema_inspector import get_schema
from app.llm.gemini import GeminiLLMClient
from app.pipeline.sql import analyze_for_sql


def main() -> None:
    load_dotenv()

    schema = get_schema()
    client = GeminiLLMClient()

    question = (
        "Which customers bought the most laptops?"
    )

    result = analyze_for_sql(
        question,
        schema,
        client,
        max_hops=3,
    )

    print("QUESTION")
    print("========")
    print(result.analysis.question)

    print()
    print("RESOLVED")
    print("========")
    print(result.analysis.clarification.resolved)

    print()
    print("INTENT")
    print("======")
    print(result.analysis.clarification.intent)

    if result.query is None:
        print()
        print(
            "SQL QUERY WAS NOT BUILT."
        )
        return

    print()
    print("SQL")
    print("===")
    print(result.sql)

    print()
    print("PARAMETERS")
    print("==========")
    print(result.parameters)


if __name__ == "__main__":
    main()