import os

from google import genai

DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"


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
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return response.text