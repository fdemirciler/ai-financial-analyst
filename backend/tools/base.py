from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd


class AnalysisTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    async def execute(
        self, data: pd.DataFrame, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Return the expected parameters schema for this tool"""
        return {"type": "object", "properties": {}, "required": []}
