from app.llm.gemini import (
    DEFAULT_GEMINI_MODEL,
    GeminiLLMClient,
)


class FakeResponse:
    def __init__(self, text: str | None):
        self.text = text


class FakeModels:
    def __init__(self):
        self.model = None
        self.contents = None
        self.config = None

    def generate_content(
        self,
        *,
        model: str,
        contents: str,
        config,
    ) -> FakeResponse:
        self.model = model
        self.contents = contents
        self.config = config

        return FakeResponse(
            '{"entity": "customers"}'
        )


class FakeGenAIClient:
    def __init__(self):
        self.models = FakeModels()


def test_gemini_client_uses_default_model(
    monkeypatch,
):
    fake_client = FakeGenAIClient()

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    monkeypatch.setattr(
        "app.llm.gemini.genai.Client",
        lambda api_key: fake_client,
    )

    client = GeminiLLMClient()

    result = client.generate(
        "Extract the database intent."
    )

    assert result == (
        '{"entity": "customers"}'
    )

    assert (
        fake_client.models.model
        == DEFAULT_GEMINI_MODEL
    )


def test_gemini_client_sends_prompt(
    monkeypatch,
):
    fake_client = FakeGenAIClient()

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    monkeypatch.setattr(
        "app.llm.gemini.genai.Client",
        lambda api_key: fake_client,
    )

    client = GeminiLLMClient()

    prompt = (
        "Extract intent for customers."
    )

    client.generate(prompt)

    assert (
        fake_client.models.contents
        == prompt
    )


def test_gemini_client_supports_custom_model(
    monkeypatch,
):
    fake_client = FakeGenAIClient()

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    monkeypatch.setattr(
        "app.llm.gemini.genai.Client",
        lambda api_key: fake_client,
    )

    client = GeminiLLMClient(
        model="custom-model",
    )

    client.generate("test")

    assert (
        fake_client.models.model
        == "custom-model"
    )


def test_gemini_client_requires_api_key(
    monkeypatch,
):
    monkeypatch.delenv(
        "GEMINI_API_KEY",
        raising=False,
    )

    try:
        GeminiLLMClient()
    except RuntimeError as exc:
        assert str(exc) == (
            "GEMINI_API_KEY environment variable "
            "is not set."
        )
    else:
        raise AssertionError(
            "Expected RuntimeError when "
            "GEMINI_API_KEY is missing."
        )


def test_gemini_client_rejects_empty_response(
    monkeypatch,
):
    fake_client = FakeGenAIClient()

    def empty_response(
        *,
        model: str,
        contents: str,
        config,
    ) -> FakeResponse:
        return FakeResponse(None)

    fake_client.models.generate_content = (
        empty_response
    )

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    monkeypatch.setattr(
        "app.llm.gemini.genai.Client",
        lambda api_key: fake_client,
    )

    client = GeminiLLMClient()

    try:
        client.generate("test")
    except RuntimeError as exc:
        assert str(exc) == (
            "Gemini returned an empty response."
        )
    else:
        raise AssertionError(
            "Expected RuntimeError for empty "
            "Gemini response."
        )


def test_gemini_client_requests_structured_json(
    monkeypatch,
):
    fake_client = FakeGenAIClient()

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    monkeypatch.setattr(
        "app.llm.gemini.genai.Client",
        lambda api_key: fake_client,
    )

    client = GeminiLLMClient()

    client.generate(
        "Extract database intent."
    )

    assert (
        fake_client.models.config
        is not None
    )

    assert (
        fake_client.models.config.response_mime_type
        == "application/json"
    )

    assert (
        fake_client.models.config.response_schema
        is not None
    )