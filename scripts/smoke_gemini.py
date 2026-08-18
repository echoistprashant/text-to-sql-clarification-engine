from dotenv import load_dotenv

from app.llm.gemini import GeminiLLMClient


def main() -> None:
    load_dotenv()

    client = GeminiLLMClient()

    prompt = """
Return ONLY valid JSON.

Use this exact structure:

{
  "entity": "customers",
  "filters": [],
  "metric": "order_items.quantity",
  "aggregation": "sum",
  "sort_direction": "desc",
  "limit": 5
}

Do not add any explanation.
""".strip()

    response = client.generate(prompt)

    print("GEMINI RESPONSE")
    print("================")
    print(response)


if __name__ == "__main__":
    main()