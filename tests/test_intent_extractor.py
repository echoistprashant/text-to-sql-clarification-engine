from app.intent.extractor import extract_intent


class FakeLLMClient:
    def __init__(self):
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)

        return """
        {
            "entity": "customers",
            "filters": [],
            "metric": null,
            "aggregation": null,
            "sort_direction": "desc",
            "limit": null
        }
        """


def test_extract_intent_uses_llm_client():
    client = FakeLLMClient()

    intent = extract_intent(
        "Which customers bought the most laptops?",
        "TABLE customers",
        client,
    )

    assert intent.entity == "customers"
    assert intent.metric is None
    assert intent.sort_direction.value == "desc"


def test_extract_intent_sends_question_to_llm():
    client = FakeLLMClient()

    question = (
        "Which customers bought the most laptops?"
    )

    extract_intent(
        question,
        "TABLE customers",
        client,
    )

    assert len(client.prompts) == 1
    assert question in client.prompts[0]
    assert (
        "Extract the user's database query intent."
        in client.prompts[0]
    )


def test_extract_intent_sends_schema_context_to_llm():
    client = FakeLLMClient()

    schema_context = """
    RELEVANT DATABASE SCHEMA:
    TABLE customers
    COLUMNS:
    - id INTEGER NOT NULL [PRIMARY KEY]
    - name VARCHAR NOT NULL
    """

    extract_intent(
        "Which customers bought the most?",
        schema_context,
        client,
    )

    assert len(client.prompts) == 1
    assert "DATABASE CONTEXT:" in client.prompts[0]
    assert "TABLE customers" in client.prompts[0]
    assert "customers.name" not in client.prompts[0]

class SalesFakeLLMClient:
    def __init__(self):
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)

        return """
        {
            "entity": "order_items",
            "filters": [
                {
                    "column": "products.name",
                    "operator": "=",
                    "value": "laptop"
                }
            ],
            "metric": "order_items.quantity",
            "aggregation": "sum",
            "sort_direction": null,
            "limit": null
        }
        """


def test_extract_intent_for_laptop_sales_uses_quantity_metric():
    client = SalesFakeLLMClient()

    intent = extract_intent(
        "How many laptops were sold?",
        """
        TABLE products
        COLUMNS:
        - id INTEGER
        - name VARCHAR

        TABLE order_items
        COLUMNS:
        - id INTEGER
        - product_id INTEGER
        - quantity INTEGER
        """,
        client,
    )

    assert intent.entity == "order_items"
    assert intent.metric == "order_items.quantity"
    assert intent.aggregation.value == "sum"
    assert len(intent.filters) == 1
    assert intent.filters[0].column == "products.name"
    assert intent.filters[0].value == "laptop"    


def test_extract_intent_prompt_defines_sales_quantity_rule():
    client = FakeLLMClient()

    extract_intent(
        "How many laptops were sold?",
        """
        TABLE products
        COLUMNS:
        - id INTEGER
        - name VARCHAR

        TABLE order_items
        COLUMNS:
        - id INTEGER
        - product_id INTEGER
        - quantity INTEGER
        """,
        client,
    )

    assert len(client.prompts) == 1

    prompt = client.prompts[0]

    assert "order_items.quantity" in prompt
    assert "How many <products> were sold?" in prompt
    assert "aggregation: \"sum\"" in prompt
    assert "COUNT(products.id)" in prompt    