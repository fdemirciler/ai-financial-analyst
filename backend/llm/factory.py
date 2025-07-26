from typing import Optional
from .base import LLMProvider
from .gemini import GeminiProvider


class LLMFactory:
    @staticmethod
    def create_provider(provider_name: str = "gemini") -> LLMProvider:
        if provider_name.lower() == "gemini":
            return GeminiProvider()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")


llm_factory = LLMFactory()
