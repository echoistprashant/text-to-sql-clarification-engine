from unittest.mock import MagicMock, patch

import httpx
import pytest

try:
    from frontend.client import (
        APIClientError,
        check_backend_health,
        execute_question,
        get_backend_url,
        submit_clarification,
    )
except ImportError:
    from client import (
        APIClientError,
        check_backend_health,
        execute_question,
        get_backend_url,
        submit_clarification,
    )


def test_get_backend_url_default(monkeypatch):
    monkeypatch.delenv("BACKEND_URL", raising=False)
    assert get_backend_url() == "http://localhost:8000"


def test_get_backend_url_custom(monkeypatch):
    monkeypatch.setenv("BACKEND_URL", "http://my-backend:8080/")
    assert get_backend_url() == "http://my-backend:8080"


def test_check_backend_health_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "ok"}

    with patch("httpx.Client.get", return_value=mock_resp):
        assert check_backend_health() is True


def test_check_backend_health_failure():
    mock_resp = MagicMock()
    mock_resp.status_code = 503

    with patch("httpx.Client.get", return_value=mock_resp):
        assert check_backend_health() is False


def test_check_backend_health_exception():
    with patch(
        "httpx.Client.get", side_effect=httpx.ConnectError("Connection refused")
    ):
        assert check_backend_health() is False


def test_execute_question_empty_raises():
    with pytest.raises(APIClientError, match="Please enter a question"):
        execute_question("")
    with pytest.raises(APIClientError, match="Please enter a question"):
        execute_question("   ")


def test_execute_question_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "question": "Show customers",
        "resolved": True,
        "sql": "SELECT name FROM customers;",
        "execution": {
            "columns": ["name"],
            "rows": [["Amit"], ["Rahul"]],
            "answer": "name: Amit\nname: Rahul",
        },
    }

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        result = execute_question("Show customers")
        assert result["resolved"] is True
        assert result["sql"] == "SELECT name FROM customers;"
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs["json"] == {"question": "Show customers"}


def test_execute_question_connect_error():
    with (
        patch(
            "httpx.Client.post", side_effect=httpx.ConnectError("Connection refused")
        ),
        pytest.raises(APIClientError, match="Backend unavailable"),
    ):
        execute_question("Show customers")


def test_execute_question_timeout():
    with (
        patch("httpx.Client.post", side_effect=httpx.TimeoutException("Timeout")),
        pytest.raises(APIClientError, match="The query took too long"),
    ):
        execute_question("Show customers")


def test_execute_question_server_error():
    mock_resp = MagicMock()
    mock_resp.status_code = 500

    with (
        patch("httpx.Client.post", return_value=mock_resp),
        pytest.raises(APIClientError, match="encountered an error"),
    ):
        execute_question("Show customers")


def test_execute_question_validation_error():
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {
        "error": {
            "code": "INVALID_REQUEST",
            "message": "Only read-only database questions are supported.",
        }
    }

    with (
        patch("httpx.Client.post", return_value=mock_resp),
        pytest.raises(
            APIClientError,
            match="Only read-only database questions are supported",
        ),
    ):
        execute_question("DELETE FROM customers")


def test_execute_question_non_json_error():
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.side_effect = ValueError("Invalid JSON")

    with (
        patch("httpx.Client.post", return_value=mock_resp),
        pytest.raises(APIClientError, match="unexpected response"),
    ):
        execute_question("test")


def test_submit_clarification_empty_raises():
    with pytest.raises(APIClientError, match="Please enter a clarification answer"):
        submit_clarification("test-id", "")


def test_submit_clarification_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "question": "Show top 5 products",
        "resolved": True,
        "sql": "SELECT name FROM products LIMIT 5;",
    }

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        result = submit_clarification("test-id", "total revenue")
        assert result["resolved"] is True
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs["json"] == {
            "analysis_id": "test-id",
            "answer": "total revenue",
        }
