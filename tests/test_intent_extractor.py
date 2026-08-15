from app.intent.extractor import extract_intent


class FakeLLMClient:
    def generate(self, prompt: str) -> str:
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
    intent = extract_intent(
        "Which customers bought the most laptops?",
        FakeLLMClient(),
    )

    assert intent.entity == "customers"
    assert intent.metric is None
    assert intent.sort_direction.value == "desc"