from unittest.mock import Mock, patch

import pytest
from google.genai import errors

from app.llm.gemini import (
    DEFAULT_GEMINI_MODEL,
    MAX_RETRIES,
    GeminiLLMClient,
)


class FakeResponse:
    def __init__(
        self,
        text: str | None,
    ):
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

    with pytest.raises(
        RuntimeError,
        match=(
            "GEMINI_API_KEY environment variable "
            "is not set."
        ),
    ):
        GeminiLLMClient()


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

    with pytest.raises(
        RuntimeError,
        match="Gemini returned an empty response.",
    ):
        client.generate("test")


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


def _server_error() -> errors.ServerError:
    return errors.ServerError(
        503,
        {
            "error": {
                "code": 503,
                "message": "Service unavailable",
                "status": "UNAVAILABLE",
            }
        },
    )


def test_gemini_client_retries_server_error_then_succeeds(
    monkeypatch,
):
    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    fake_client = FakeGenAIClient()

    response = FakeResponse(
        '{"entity": "customers"}'
    )

    fake_client.models.generate_content = Mock(
        side_effect=[
            _server_error(),
            response,
        ]
    )

    monkeypatch.setattr(
        "app.llm.gemini.genai.Client",
        lambda api_key: fake_client,
    )

    client = GeminiLLMClient()

    with patch(
        "app.llm.gemini.time.sleep"
    ) as sleep:
        result = client.generate(
            "Show all customers"
        )

    assert result == (
        '{"entity": "customers"}'
    )

    assert (
        fake_client.models.generate_content.call_count
        == 2
    )

    sleep.assert_called_once_with(1.0)


def test_gemini_client_retries_server_errors_with_backoff(
    monkeypatch,
):
    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    fake_client = FakeGenAIClient()

    response = FakeResponse(
        '{"entity": "customers"}'
    )

    fake_client.models.generate_content = Mock(
        side_effect=[
            _server_error(),
            _server_error(),
            response,
        ]
    )

    monkeypatch.setattr(
        "app.llm.gemini.genai.Client",
        lambda api_key: fake_client,
    )

    client = GeminiLLMClient()

    with patch(
        "app.llm.gemini.time.sleep"
    ) as sleep:
        result = client.generate(
            "Show all customers"
        )

    assert result == (
        '{"entity": "customers"}'
    )

    assert (
        fake_client.models.generate_content.call_count
        == 3
    )

    assert sleep.call_args_list == [
        ((1.0,),),
        ((2.0,),),
    ]


def test_gemini_client_stops_after_max_retries(
    monkeypatch,
):
    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    fake_client = FakeGenAIClient()

    fake_client.models.generate_content = Mock(
        side_effect=_server_error()
    )

    monkeypatch.setattr(
        "app.llm.gemini.genai.Client",
        lambda api_key: fake_client,
    )

    client = GeminiLLMClient()

    with patch(
        "app.llm.gemini.time.sleep"
    ) as sleep, pytest.raises(
        errors.ServerError
    ):
        client.generate(
            "Show all customers"
        )

    assert (
        fake_client.models.generate_content.call_count
        == MAX_RETRIES + 1
    )

    assert sleep.call_count == MAX_RETRIES


def test_gemini_client_does_not_retry_non_server_error(
    monkeypatch,
):
    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    fake_client = FakeGenAIClient()

    error = RuntimeError(
        "Permanent failure"
    )

    fake_client.models.generate_content = Mock(
        side_effect=error
    )

    monkeypatch.setattr(
        "app.llm.gemini.genai.Client",
        lambda api_key: fake_client,
    )

    client = GeminiLLMClient()

    with patch(
        "app.llm.gemini.time.sleep"
    ) as sleep, pytest.raises(
        RuntimeError,
        match="Permanent failure",
    ):
        client.generate(
            "Show all customers"
        )

    assert (
        fake_client.models.generate_content.call_count
        == 1
    )

    sleep.assert_not_called()