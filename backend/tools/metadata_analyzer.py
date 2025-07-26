import pandas as pd
from typing import Dict, Any
from .base import AnalysisTool


class MetadataAnalyzer(AnalysisTool):
    @property
    def name(self) -> str:
        return "metadata_analyzer"

    @property
    def description(self) -> str:
        return "Analyzes data structure and provides metadata"

    async def execute(
        self, data: pd.DataFrame, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            metadata = {
                "shape": data.shape,
                "columns": [],
                "data_types": {},
                "missing_values": {},
                "numeric_columns": [],
                "categorical_columns": [],
                "date_columns": [],
            }

            for column in data.columns:
                col_info = {
                    "name": str(column),
                    "dtype": str(data[column].dtype),
                    "null_count": int(data[column].isnull().sum()),
                    "unique_count": int(data[column].nunique()),
                }

                metadata["columns"].append(col_info)
                metadata["data_types"][str(column)] = str(data[column].dtype)
                metadata["missing_values"][str(column)] = int(
                    data[column].isnull().sum()
                )

                # Categorize columns
                if pd.api.types.is_numeric_dtype(data[column]):
                    metadata["numeric_columns"].append(str(column))
                elif pd.api.types.is_datetime64_any_dtype(data[column]):
                    metadata["date_columns"].append(str(column))
                else:
                    metadata["categorical_columns"].append(str(column))

            return {
                "success": True,
                "metadata": metadata,
                "message": "Metadata analysis completed",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to analyze metadata: {str(e)}",
            }
