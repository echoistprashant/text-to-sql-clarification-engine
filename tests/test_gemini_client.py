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


class FakeChat:
    def __init__(self):
        self.model = None
        self.config = None
        self.contents = None

        self.send_message = Mock(
            side_effect=self._send_message,
        )

    def configure(
        self,
        *,
        model: str,
        config,
    ):
        self.model = model
        self.config = config

    def _send_message(
        self,
        prompt: str,
    ) -> FakeResponse:
        self.contents = prompt

        return FakeResponse(
            '{"entity": "customers"}'
        )

class FakeChats:
    def __init__(self):
        self.model = None
        self.config = None
        self.contents = None
        self.chat = FakeChat()

    def create(
        self,
        *,
        model: str,
        config,
    ) -> FakeChat:
        self.model = model
        self.config = config

        self.chat.configure(
            model=model,
            config=config,
        )

        return self.chat


class FakeGenAIClient:
    def __init__(
        self,
        api_key: str,
        http_options=None,
    ):
        self.api_key = api_key
        self.http_options = http_options
        self.chats = FakeChats()


def _patch_genai_client(
    monkeypatch,
    fake_client: FakeGenAIClient,
):
    def create_client(
        api_key: str,
        http_options=None,
    ):
        fake_client.api_key = api_key
        fake_client.http_options = http_options

        return fake_client

    monkeypatch.setattr(
        "app.llm.gemini.genai.Client",
        create_client,
    )


def test_gemini_client_uses_default_model(
    monkeypatch,
):
    fake_client = FakeGenAIClient(
        api_key="test-key",
    )

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    _patch_genai_client(
        monkeypatch,
        fake_client,
    )

    client = GeminiLLMClient()

    result = client.generate(
        "Extract the database intent."
    )

    assert result == (
        '{"entity": "customers"}'
    )

    assert (
        fake_client.chats.model
        == DEFAULT_GEMINI_MODEL
    )


def test_gemini_client_sends_prompt(
    monkeypatch,
):
    fake_client = FakeGenAIClient(
        api_key="test-key",
    )

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    _patch_genai_client(
        monkeypatch,
        fake_client,
    )

    client = GeminiLLMClient()

    prompt = (
        "Extract intent for customers."
    )

    client.generate(prompt)

    assert (
        fake_client.chats.chat.contents
        == prompt
    )

    fake_client.chats.chat.send_message.assert_called_once_with(
        prompt,
    )


def test_gemini_client_supports_custom_model(
    monkeypatch,
):
    fake_client = FakeGenAIClient(
        api_key="test-key",
    )

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    _patch_genai_client(
        monkeypatch,
        fake_client,
    )

    client = GeminiLLMClient(
        model="custom-model",
    )

    client.generate("test")

    assert (
        fake_client.chats.model
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
    fake_client = FakeGenAIClient(
        api_key="test-key",
    )

    fake_client.chats.chat.send_message = Mock(
        return_value=FakeResponse(None)
    )

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    _patch_genai_client(
        monkeypatch,
        fake_client,
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
    fake_client = FakeGenAIClient(
        api_key="test-key",
    )

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    _patch_genai_client(
        monkeypatch,
        fake_client,
    )

    client = GeminiLLMClient()

    client.generate(
        "Extract database intent."
    )

    assert (
        fake_client.chats.config
        is not None
    )

    assert (
        fake_client.chats.config.response_mime_type
        == "application/json"
    )

    assert (
        fake_client.chats.config.response_schema
        is not None
    )


def test_gemini_client_uses_configured_timeout(
    monkeypatch,
):
    fake_client = FakeGenAIClient(
        api_key="test-key",
    )

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    monkeypatch.setenv(
        "GEMINI_TIMEOUT_SECONDS",
        "45",
    )

    _patch_genai_client(
        monkeypatch,
        fake_client,
    )

    client = GeminiLLMClient()

    client.generate(
        "Extract database intent."
    )

    assert (
        fake_client.http_options
        is not None
    )

    assert (
        fake_client.http_options.timeout
        == 45000
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

    fake_client = FakeGenAIClient(
        api_key="test-key",
    )

    fake_client.chats.chat.send_message = Mock(
        side_effect=[
            _server_error(),
            FakeResponse(
                '{"entity": "customers"}'
            ),
        ]
    )

    _patch_genai_client(
        monkeypatch,
        fake_client,
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
        fake_client.chats.chat.send_message.call_count
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

    fake_client = FakeGenAIClient(
        api_key="test-key",
    )

    fake_client.chats.chat.send_message = Mock(
        side_effect=[
            _server_error(),
            _server_error(),
            FakeResponse(
                '{"entity": "customers"}'
            ),
        ]
    )

    _patch_genai_client(
        monkeypatch,
        fake_client,
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
        fake_client.chats.chat.send_message.call_count
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

    fake_client = FakeGenAIClient(
        api_key="test-key",
    )

    fake_client.chats.chat.send_message = Mock(
        side_effect=_server_error()
    )

    _patch_genai_client(
        monkeypatch,
        fake_client,
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
        fake_client.chats.chat.send_message.call_count
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

    fake_client = FakeGenAIClient(
        api_key="test-key",
    )

    error = RuntimeError(
        "Permanent failure"
    )

    fake_client.chats.chat.send_message = Mock(
        side_effect=error
    )

    _patch_genai_client(
        monkeypatch,
        fake_client,
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
        fake_client.chats.chat.send_message.call_count
        == 1
    )

    sleep.assert_not_called()