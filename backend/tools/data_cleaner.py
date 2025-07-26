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
            cleaned_data = data.copy()
            exclude_columns = parameters.get("exclude_columns", [])

            # Standardize column names and update exclude_columns list accordingly
            standardized_exclude = []
            new_columns = {}
            for col in cleaned_data.columns:
                new_col_name = str(col).lower().replace(" ", "_")
                new_columns[col] = new_col_name
                if col in exclude_columns:
                    standardized_exclude.append(new_col_name)

            cleaned_data.rename(columns=new_columns, inplace=True)

            # 1. Sanitize and convert data types, skipping excluded columns
            for col in cleaned_data.columns:
                if col in standardized_exclude:
                    continue

                # Sanitize potential numeric columns
                if cleaned_data[col].dtype == "object":
                    # Remove currency symbols, commas, and whitespace
                    if cleaned_data[col].astype(str).str.contains(r"[\$,€]").any():
                        cleaned_data[col] = (
                            cleaned_data[col]
                            .astype(str)
                            .str.replace(r"[$,€]", "", regex=True)
                            .str.replace(",", "")
                            .str.strip()
                        )

                    # Attempt to convert to numeric
                    cleaned_data[col] = pd.to_numeric(
                        cleaned_data[col], errors="coerce"
                    )

                # Attempt to convert to datetime
                if cleaned_data[col].dtype == "object":
                    cleaned_data[col] = pd.to_datetime(
                        cleaned_data[col], errors="coerce"
                    )

            # 2. Handle missing values
            for col in cleaned_data.columns:
                if col not in standardized_exclude:
                    if cleaned_data[col].dtype in ["float64", "int64"]:
                        cleaned_data[col] = cleaned_data[col].fillna(0)
                    elif cleaned_data[col].dtype == "object":
                        cleaned_data[col] = cleaned_data[col].fillna("")

            # 3. Remove rows and columns that are completely empty
            cleaned_data.dropna(how="all", inplace=True)
            cleaned_data.dropna(axis=1, how="all", inplace=True)

            # 4. Ensure JSON-serializable output
            # Convert NaT to None for JSON compatibility
            for col in cleaned_data.select_dtypes(include=["datetime64[ns]"]).columns:
                cleaned_data[col] = (
                    cleaned_data[col]
                    .astype(object)
                    .where(cleaned_data[col].notna(), None)
                )

            json_output = cleaned_data.to_dict("records")
            dtypes = cleaned_data.dtypes.astype(str).to_dict()

            return {
                "success": True,
                "data": json_output,
                "dtypes": dtypes,
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
