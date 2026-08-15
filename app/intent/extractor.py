from app.intent.models import QueryIntent
from app.intent.parser import parse_intent_response
from app.llm.client import LLMClient


def extract_intent(
    question: str,
    llm_client: LLMClient,
) -> QueryIntent:
    prompt = f"""
Extract the user's database query intent.

Return ONLY valid JSON with this structure:

{{
  "entity": null,
  "filters": [],
  "metric": null,
  "aggregation": null,
  "sort_direction": null,
  "limit": null
}}

Question:
{question}
""".strip()

    response = llm_client.generate(prompt)

    return parse_intent_response(response)