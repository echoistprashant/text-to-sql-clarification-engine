import os
import time

from google import genai
from google.genai import errors, types

from app.llm.schemas import INTENT_RESPONSE_SCHEMA

DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"

MAX_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 1.0


class GeminiLLMClient:
    def __init__(
        self,
        model: str = DEFAULT_GEMINI_MODEL,
    ) -> None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable "
                "is not set."
            )

        self._client = genai.Client(
            api_key=api_key,
        )
        self._model = model

    def generate(self, prompt: str) -> str:
        for attempt in range(MAX_RETRIES + 1):
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
                if attempt >= MAX_RETRIES:
                    raise

                delay = (
                    INITIAL_RETRY_DELAY_SECONDS
                    * (2**attempt)
                )
                time.sleep(delay)