from unittest.mock import MagicMock, patch

import httpx
import pytest
from app.llm.openrouter import DEFAULT_OPENROUTER_MODEL, OpenRouterLLMClient


def test_openrouter_client_init_defaults():
    client = OpenRouterLLMClient(api_key="sk-test-123")
    assert client._api_key == "sk-test-123"
    assert client._model == DEFAULT_OPENROUTER_MODEL


def test_openrouter_client_missing_key_raises(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with patch("app.llm.openrouter.get_settings") as mock_settings:
        mock_settings.return_value.openrouter_api_key = None
        with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY is not set"):
            OpenRouterLLMClient(api_key=None)


def test_openrouter_client_generate_success():
    client = OpenRouterLLMClient(api_key="sk-test-123", model="test-model")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": '{"entity": "customers"}'}}]
    }
    mock_resp.raise_for_status.return_value = None

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        result = client.generate("Show customers")
        assert result == '{"entity": "customers"}'
        assert mock_post.called
        kwargs = mock_post.call_args[1]
        assert kwargs["json"]["model"] == "test-model"
        assert kwargs["json"]["max_tokens"] == 1000


def test_openrouter_client_empty_response_raises():
    client = OpenRouterLLMClient(api_key="sk-test-123")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"choices": [{"message": {"content": ""}}]}
    mock_resp.raise_for_status.return_value = None

    with (
        patch("httpx.Client.post", return_value=mock_resp),
        pytest.raises(RuntimeError, match="empty response"),
    ):
        client.generate("test")


def test_openrouter_client_retries_on_500():
    client = OpenRouterLLMClient(api_key="sk-test-123")
    client._initial_retry_delay = 0.01

    mock_fail = MagicMock()
    mock_fail.status_code = 502
    mock_fail.request = MagicMock()

    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {
        "choices": [{"message": {"content": '{"status": "ok"}'}}]
    }
    mock_success.raise_for_status.return_value = None

    with patch(
        "httpx.Client.post",
        side_effect=[
            httpx.HTTPStatusError(
                "502 Server Error", request=mock_fail.request, response=mock_fail
            ),
            mock_success,
        ],
    ):
        result = client.generate("test")
        assert result == '{"status": "ok"}'
