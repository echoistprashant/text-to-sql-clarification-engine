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
  "limit": null,
  "group_by": null
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

7. "group_by" must be either null or a fully qualified
   table.column name.

   Correct:
   "customers.name"
   "products.name"
   "products.category"
   "orders.status"

   Incorrect:
   "name"
   "category"
   "status"

8. Do not invent tables, columns, relationships, or values.

9. If the question refers to a column without naming its table,
   infer the table ONLY when exactly one matching column exists
   in the provided schema.

10. If multiple tables contain a column with the same name and
    the correct table cannot be determined, return null rather
    than guessing.

11. Preserve filter values exactly as represented by the user
    or by the provided schema values.

12. If the question does not provide enough information for a
    field, return null or an empty list as appropriate.

13. For every filter, verify that the table.column combination
    actually exists in the provided schema before returning it.

14. Ranking language such as "most", "least", "highest",
    "lowest", "top", "best", or "worst" does NOT by itself
    identify a metric.

    If the question asks for a ranking but does not explicitly
    specify what is being measured, return:

    "metric": null

    and preserve the requested sort direction.

    Examples:

    "Which customers bought the most laptops?"
      -> metric: null
      -> aggregation: null
      -> sort_direction: "desc"

    "Which customers placed the most orders?"
      -> metric: null
      -> aggregation: null
      -> sort_direction: "desc"

    "Which customers spent the most?"
      -> metric: null
      -> aggregation: null
      -> sort_direction: "desc"

    "Which products sold the most?"
      -> metric: null
      -> aggregation: null
      -> sort_direction: "desc"

15. For explicit quantity questions about products, units, items,
    sales, purchases, or orders, use a quantity metric when the
    schema provides "order_items.quantity".

    In particular, when the question asks:

    "How many <products> were sold?"
    "How many <products> were purchased?"
    "How many units were sold?"
    "How many items were sold?"
    "How many units of <product> were purchased?"

    and "order_items.quantity" exists in the provided schema:

      -> metric: "order_items.quantity"
      -> aggregation: "sum"

    Do NOT interpret these questions as COUNT(products.id),
    because counting product rows does not represent the number
    of units sold or purchased.

    Example:

    "How many laptops were sold?"
      -> metric: "order_items.quantity"
      -> aggregation: "sum"

16. When a product name or product category is mentioned in a
    sales or purchase question, use the provided product schema
    values to identify the appropriate product filter.

    For example, if the schema contains:

    products.name = "Laptop Pro 15"

    and the question is:

    "How many laptops were sold?"

    the intent may use:

      entity: "order_items"
      metric: "order_items.quantity"
      aggregation: "sum"

    with a filter referring to the product name when the schema
    context provides a reliable match.

17. Do not infer an arbitrary metric merely from a verb.

    However, explicit quantity language combined with a sales,
    purchase, or order context is sufficient to select
    "order_items.quantity" when that column exists.

18. For ranking questions, continue to require clarification
    when the metric is genuinely unspecified.

    Do NOT apply the quantity rule from rule 15 to ranking
    questions such as:

    "Which customers bought the most laptops?"

    That question should remain:

      -> metric: null
      -> aggregation: null
      -> sort_direction: "desc"

    because "most" does not specify whether the ranking should
    be based on units, orders, or spending.

19. Never return a metric or filter column that does not exist
    in the provided database schema.

20. Use "group_by" when the question explicitly asks for a
    metric broken down, grouped, summarized, or reported
    "by" another dimension.

    Examples:

    "Show revenue by customer"
      -> entity: "orders"
      -> metric: "orders.total_amount"
      -> aggregation: "sum"
      -> group_by: "customers.name"

    "Show sales by product"
      -> entity: "orders"
      -> metric: "orders.total_amount"
      -> aggregation: "sum"
      -> group_by: "products.name"

    "Show revenue by category"
      -> entity: "orders"
      -> metric: "orders.total_amount"
      -> aggregation: "sum"
      -> group_by: "products.category"

21. When a question asks for a total without a grouping
    dimension, "group_by" must be null.

    Example:

    "What is the total revenue?"
      -> entity: "orders"
      -> metric: "orders.total_amount"
      -> aggregation: "sum"
      -> group_by: null

22. "group_by" must reference an actual column in the
    provided database schema.

23. If the grouping dimension belongs to a different table
    from the entity or metric table, use the appropriate
    table.column from the schema.

    Example:

    "Show revenue by customer"

    If the schema contains:

      orders.customer_id -> customers.id
      orders.total_amount
      customers.name

    then use:

      entity: "orders"
      metric: "orders.total_amount"
      aggregation: "sum"
      group_by: "customers.name"

24. Do not confuse "group_by" with a filter.

    "Show revenue for customers from India"

    means:

      group_by: null

    and the customer country should be represented as a filter,
    for example:

      "customers.country" = "India"

25. If the question explicitly says "by customer", "per customer",
    "for each customer", or equivalent wording, use a customer
    dimension when the schema provides a suitable customer
    column.

    Prefer:

      "customers.name"

    when that column exists.

26. If the question explicitly says "by product", "per product",
    "for each product", or equivalent wording, use a product
    dimension when the schema provides a suitable product
    column.

    Prefer:

      "products.name"

    when that column exists.

27. If the question explicitly says "by category", "per category",
    "for each category", or equivalent wording, use:

      "products.category"

    when that column exists.

28. A grouped aggregate may also be ranked.

    Example:

    "Show the top 5 customers by revenue"

    should use:

      metric: "orders.total_amount"
      aggregation: "sum"
      group_by: "customers.name"
      sort_direction: "desc"
      limit: 5

29. Ranking still requires an explicit metric.

    Example:

    "Show the top 5 customers"

    should NOT invent a metric.

    Return:

      metric: null
      aggregation: null
      group_by: "customers.name"
      sort_direction: "desc"
      limit: 5

    This allows the clarification system to ask what
    "top" should be measured by.

30. Do not use "group_by" merely because multiple tables are
    involved.

    A JOIN is required only when the query actually needs a
    column from another table.

31. The final intent must contain only tables and columns that
    exist in the provided database schema.

DATABASE CONTEXT:
{schema_context}

USER QUESTION:
{question}
""".strip()

    response = llm_client.generate(prompt)

    return parse_intent_response(response)