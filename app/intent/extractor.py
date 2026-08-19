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

Return ONLY valid JSON with this exact structure:

{{
  "entity": null,
  "filters": [],
  "metric": null,
  "aggregation": null,
  "sort_direction": null,
  "limit": null
}}

Rules:

1. "entity" must be exactly one table name from the provided schema.

2. Every filter "column" MUST be a fully qualified
   table.column name.

   Correct:
   "customers.country"
   "products.price"
   "orders.customer_id"
   "order_items.quantity"

   Incorrect:
   "country"
   "price"
   "customer_id"
   "quantity"

3. "metric" must also be a fully qualified
   table.column name.

   Correct:
   "order_items.quantity"
   "orders.total_amount"
   "products.price"

4. "aggregation" must be one of:
   "count", "sum", "avg", "min", "max", or null.

5. "sort_direction" must be:
   "asc", "desc", or null.

6. "limit" must be a positive integer or null.

7. Do not invent tables, columns, relationships, or values.

8. If the question refers to a column without naming its table,
   infer the table ONLY when exactly one matching column exists
   in the provided schema.

9. If multiple tables contain a column with the same name and
   the correct table cannot be determined, return null rather
   than guessing.

10. Preserve filter values exactly as represented by the user
    or by the provided schema values.

11. If the question does not provide enough information for a
    field, return null or an empty list as appropriate.

12. For every filter, verify that the table.column combination
    actually exists in the provided schema before returning it.

DATABASE CONTEXT:
{schema_context}

USER QUESTION:
{question}
""".strip()

    response = llm_client.generate(prompt)

    return parse_intent_response(response)