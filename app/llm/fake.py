class FakeLLMClient:
    """Deterministic LLM client for development and testing."""

    def __init__(self, response: str):
        self.response = response
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response