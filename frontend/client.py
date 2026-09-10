import os
from typing import Any

import httpx

DEFAULT_BACKEND_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 30.0


def get_backend_url() -> str:
    """Return configured backend URL stripped of trailing slashes."""
    raw_url = os.getenv("BACKEND_URL", DEFAULT_BACKEND_URL)
    return raw_url.rstrip("/")


def check_backend_health(backend_url: str | None = None) -> bool:
    """Check if the backend /health endpoint returns status ok."""
    url = f"{backend_url or get_backend_url()}/health"
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("status") == "ok"
            return False
    except (httpx.HTTPError, ValueError):
        return False


class APIClientError(Exception):
    """Safe, user-facing client error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def execute_question(
    question: str,
    backend_url: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """
    Send a natural language question to POST /execute.

    Returns the parsed JSON dictionary from the backend.
    Raises APIClientError with safe, human-readable error messages.
    """
    cleaned_question = question.strip()
    if not cleaned_question:
        raise APIClientError("Please enter a question.")

    base_url = backend_url or get_backend_url()
    endpoint = f"{base_url}/execute"

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                endpoint,
                json={"question": cleaned_question},
            )
    except httpx.ConnectError:
        raise APIClientError(
            "Backend unavailable. Please make sure the FastAPI service is running."
        ) from None
    except httpx.TimeoutException:
        raise APIClientError("The query took too long. Please try again.") from None
    except httpx.TransportError:
        raise APIClientError(
            "Backend unavailable. Please make sure the FastAPI service is running."
        ) from None

    return _handle_response(response)


def submit_clarification(
    analysis_id: str,
    answer: str,
    backend_url: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """
    Send a clarification answer to POST /execute/clarification.

    Returns the parsed JSON dictionary from the backend.
    Raises APIClientError with safe, human-readable error messages.
    """
    cleaned_answer = answer.strip()
    if not cleaned_answer:
        raise APIClientError("Please enter a clarification answer.")

    base_url = backend_url or get_backend_url()
    endpoint = f"{base_url}/execute/clarification"

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                endpoint,
                json={
                    "analysis_id": analysis_id,
                    "answer": cleaned_answer,
                },
            )
    except httpx.ConnectError:
        raise APIClientError(
            "Backend unavailable. Please make sure the FastAPI service is running."
        ) from None
    except httpx.TimeoutException:
        raise APIClientError("The query took too long. Please try again.") from None
    except httpx.TransportError:
        raise APIClientError(
            "Backend unavailable. Please make sure the FastAPI service is running."
        ) from None

    return _handle_response(response)


def _handle_response(response: httpx.Response) -> dict[str, Any]:
    """Parse HTTP response and map errors to safe human-readable messages."""
    if response.status_code >= 500:
        raise APIClientError(
            "The backend encountered an error while processing the query.",
            status_code=response.status_code,
        )

    try:
        data = response.json()
    except (ValueError, TypeError):
        raise APIClientError(
            "The backend returned an unexpected response.",
            status_code=response.status_code,
        ) from None

    if response.status_code >= 400:
        message = _extract_error_message(data)
        raise APIClientError(message, status_code=response.status_code)

    if not isinstance(data, dict):
        raise APIClientError("The backend returned an unexpected response.")

    return data


def _extract_error_message(data: Any) -> str:
    """Extract a safe message from standard FastAPI error payloads."""
    if isinstance(data, dict):
        # Format: {"error": {"code": "...", "message": "..."}}
        err = data.get("error")
        if isinstance(err, dict) and "message" in err:
            return str(err["message"])
        if isinstance(err, str):
            return err

        # Format: {"detail": "..."}
        detail = data.get("detail")
        if isinstance(detail, str):
            return detail
        if isinstance(detail, list) and detail and isinstance(detail[0], dict):
            return str(detail[0].get("msg", "Request validation failed."))

    return "The backend rejected the request."
