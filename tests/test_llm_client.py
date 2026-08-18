from app.llm.fake import FakeLLMClient


def test_fake_llm_client_returns_configured_response():
    client = FakeLLMClient(
        '{"entity": "customers"}'
    )

    response = client.generate(
        "Extract the intent."
    )

    assert response == '{"entity": "customers"}'


def test_fake_llm_client_records_prompts():
    client = FakeLLMClient(
        '{"entity": "customers"}'
    )

    prompt = "Extract the intent."

    client.generate(prompt)

    assert client.prompts == [
        prompt,
    ]


def test_fake_llm_client_records_multiple_prompts():
    client = FakeLLMClient(
        '{"entity": "customers"}'
    )

    client.generate("first")
    client.generate("second")

    assert client.prompts == [
        "first",
        "second",
    ]