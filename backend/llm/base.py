from abc import ABC, abstractmethod
from typing import Dict, Any, List


class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        pass

    @abstractmethod
    async def generate_structured_response(
        self, prompt: str, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        pass
