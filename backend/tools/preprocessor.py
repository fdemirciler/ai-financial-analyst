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
                # First try direct numeric conversion
                numeric_series = pd.to_numeric(data[col], errors="coerce")

                # If direct conversion fails, try cleaning and then converting
                if numeric_series.notna().sum() / len(data) < 0.5:
                    # Try cleaning currency symbols and commas first
                    cleaned_series = (
                        data[col]
                        .astype(str)
                        .str.replace(r"[$,€]", "", regex=True)
                        .str.replace(",", "")
                        .str.strip()
                    )
                    cleaned_numeric = pd.to_numeric(cleaned_series, errors="coerce")

                    # If still less than 50% convertible after cleaning, exclude the column
                    if cleaned_numeric.notna().sum() / len(data) < 0.5:
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
