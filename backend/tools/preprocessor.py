import pandas as pd
from typing import Dict, Any, List
from .base import AnalysisTool


class DataPreprocessor(AnalysisTool):
    @property
    def name(self) -> str:
        return "data_preprocessor"

    @property
    def description(self) -> str:
        return "Analyzes data columns to identify their types (numeric, categorical, date) and determines which columns should be excluded from numeric cleaning."

    async def execute(
        self, data: pd.DataFrame, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            # Identify non-numeric columns to be excluded from cleaning
            exclude_columns = []
            for col in data.columns:
                # Attempt to convert to numeric, coercing errors
                numeric_series = pd.to_numeric(data[col], errors="coerce")
                # If a column has a low percentage of numeric values, consider it non-numeric
                if numeric_series.notna().sum() / len(data) < 0.5:
                    exclude_columns.append(str(col))

            return {
                "success": True,
                "exclude_columns": exclude_columns,
                "message": f"Preprocessing complete. Identified {len(exclude_columns)} columns to exclude from numeric cleaning.",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to preprocess data: {str(e)}",
            }
