import logging
import time

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_MODEL = "google/gemini-2.5-flash"


class OpenRouterLLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_settings()

        self._api_key = api_key or settings.openrouter_api_key
        if not self._api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set.")

        self._model = model or settings.openrouter_model or DEFAULT_OPENROUTER_MODEL
        self._max_retries = settings.llm_max_retries
        self._initial_retry_delay = settings.llm_initial_retry_delay_seconds
        self._timeout = settings.llm_timeout_seconds

    def generate(
        self,
        prompt: str,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/echoistprashant/text-to-sql-clarification-engine",
            "X-Title": "Text-to-SQL Clarification Engine",
        }

        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 1000,
            "temperature": 0.0,
        }

        delay = self._initial_retry_delay

        for attempt in range(self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(
                        OPENROUTER_URL,
                        headers=headers,
                        json=payload,
                    )

                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"Server error: {response.status_code}",
                        request=response.request,
                        response=response,
                    )

                response.raise_for_status()

                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    raise RuntimeError("OpenRouter returned no choices in response.")

                content = choices[0].get("message", {}).get("content")
                if not content:
                    raise RuntimeError("OpenRouter returned an empty response.")

                return content.strip()

            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                is_server_error = (
                    isinstance(exc, httpx.HTTPStatusError)
                    and exc.response.status_code >= 500
                )
                is_transport_error = isinstance(exc, httpx.TransportError)

                if (
                    is_server_error or is_transport_error
                ) and attempt < self._max_retries:
                    logger.warning(
                        "OpenRouter call failed (attempt %d/%d): %s. Retrying in %.1fs...",
                        attempt + 1,
                        self._max_retries,
                        exc,
                        delay,
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise
