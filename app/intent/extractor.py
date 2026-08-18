from app.intent.models import QueryIntent
from app.intent.parser import parse_intent_response
from app.llm.client import LLMClient


def extract_intent(
    question: str,
    schema_context: str,
    llm_client: LLMClient,
) -> QueryIntent:
    prompt = f"""
Extract the user's database query intent.

Use ONLY the database schema and values provided below.

Return ONLY valid JSON with this structure:

{{
  "entity": null,
  "filters": [],
  "metric": null,
  "aggregation": null,
  "sort_direction": null,
  "limit": null
}}

Rules:
- "entity" must refer to a table from the provided schema.
- Filter columns must refer to columns from the provided schema.
- "metric" must be a qualified column such as "order_items.quantity".
- "aggregation" must be one of:
  "count", "sum", "avg", "min", "max", or null.
- "sort_direction" must be "asc", "desc", or null.
- "limit" must be a positive integer or null.
- Do not invent tables, columns, relationships, or values.
- If the question does not provide enough information for a field,
  return null or an empty list as appropriate.

DATABASE CONTEXT:
{schema_context}

USER QUESTION:
{question}
""".strip()

    response = llm_client.generate(prompt)

    return parse_intent_response(response)