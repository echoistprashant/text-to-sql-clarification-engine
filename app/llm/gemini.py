import time

from google import genai
from google.genai import errors, types

from app.config import get_settings
from app.llm.schemas import INTENT_RESPONSE_SCHEMA

DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"

MAX_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 1.0


class GeminiLLMClient:
    def __init__(
        self,
        model: str | None = None,
    ) -> None:
        settings = get_settings()

        self._client = genai.Client(
            api_key=settings.gemini_api_key,
        )

        self._model = (
            model
            if model is not None
            else settings.gemini_model
        )

        self._max_retries = (
            settings.gemini_max_retries
        )

        self._initial_retry_delay_seconds = (
            settings.gemini_initial_retry_delay_seconds
        )

    def generate(
        self,
        prompt: str,
    ) -> str:
        for attempt in range(
            self._max_retries + 1,
        ):
            try:
                response = (
                    self._client.models.generate_content(
                        model=self._model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=(
                                INTENT_RESPONSE_SCHEMA
                            ),
                        ),
                    )
                )

                if not response.text:
                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                return response.text

            except errors.ServerError:
                if attempt >= self._max_retries:
                    raise

                delay = (
                    self._initial_retry_delay_seconds
                    * (2**attempt)
                )

                time.sleep(delay)

        raise RuntimeError(
            "Gemini generation failed."
        )