from dotenv import load_dotenv

from app.db.schema_inspector import get_schema
from app.llm.gemini import GeminiLLMClient
from app.pipeline.analysis import analyze_question


def main() -> None:
    load_dotenv()

    schema = get_schema()

    client = GeminiLLMClient()

    question = (
        "Which customers bought the most laptops?"
    )

    result = analyze_question(
        question,
        schema,
        client,
        max_hops=3,
    )

    print("QUESTION")
    print("========")
    print(result.question)

    print()
    print("RETRIEVED TABLES")
    print("================")
    for table in result.schema.tables:
        print(f"- {table}")

    print()
    print("VALUE MATCHES")
    print("=============")
    for match in result.schema.value_matches:
        print(
            f"- {match.table_name}."
            f"{match.column_name} = "
            f"{match.value}"
        )

    print()
    print("JOIN PATH")
    print("=========")
    print(
        " -> ".join(
            result.schema.join_path
        )
    )

    print()
    print("INTENT")
    print("======")
    print(result.clarification.intent)

    print()
    print("RESOLVED")
    print("========")
    print(result.clarification.resolved)

    if result.clarification.clarification:
        print()
        print("CLARIFICATION")
        print("=============")
        print(
            result.clarification.clarification
        )


if __name__ == "__main__":
    main()