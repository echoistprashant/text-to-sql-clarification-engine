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