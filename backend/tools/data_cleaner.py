import pandas as pd
from typing import Dict, Any
from .base import AnalysisTool


class DataCleaner(AnalysisTool):
    @property
    def name(self) -> str:
        return "data_cleaner"

    @property
    def description(self) -> str:
        return "Cleans and standardizes uploaded data"

    async def execute(
        self, data: pd.DataFrame, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            # Make a copy to avoid modifying original data
            cleaned_data = data.copy()

            # Remove completely empty rows and columns
            cleaned_data = cleaned_data.dropna(how="all")
            cleaned_data = cleaned_data.dropna(axis=1, how="all")

            # Convert column names to lowercase and replace spaces with underscores
            cleaned_data.columns = [
                str(col).lower().replace(" ", "_") for col in cleaned_data.columns
            ]

            # Handle common data type conversions
            for col in cleaned_data.columns:
                # Try to convert to numeric if possible
                if cleaned_data[col].dtype == "object":
                    cleaned_data[col] = pd.to_numeric(
                        cleaned_data[col], errors="ignore"
                    )

                # Convert date strings to datetime if possible
                if cleaned_data[col].dtype == "object":
                    try:
                        cleaned_data[col] = pd.to_datetime(
                            cleaned_data[col], errors="ignore"
                        )
                    except:
                        pass

            return {
                "success": True,
                "data": cleaned_data.to_dict("records"),
                "shape": cleaned_data.shape,
                "columns": list(cleaned_data.columns),
                "message": f"Data cleaned successfully. Shape: {cleaned_data.shape}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to clean data: {str(e)}",
            }
