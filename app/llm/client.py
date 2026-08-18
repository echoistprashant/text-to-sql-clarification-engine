from typing import Protocol


class LLMClient(Protocol):
    """Interface for a text-generating language model."""

    def generate(self, prompt: str) -> str:
        """
        Generate a text response from the LLM.

        Args:
            prompt: Prompt sent to the language model.

        Returns:
            Raw text returned by the language model.

        Raises:
            Exception:
                Provider-specific failures may be propagated to the
                caller and handled at a higher application layer.
        """
        ...