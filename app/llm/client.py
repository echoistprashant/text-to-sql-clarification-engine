from typing import Protocol


class LLMClient(Protocol):
    def generate(self, prompt: str) -> str:
        """Generate a text response from the LLM."""
        ...