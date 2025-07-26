import pandas as pd
from typing import Dict, Any, List
from .base import AnalysisTool


class DataProfiler(AnalysisTool):
    @property
    def name(self) -> str:
        return "data_profiler"

    @property
    def description(self) -> str:
        return "Creates a comprehensive profile of cleaned data including metrics, periods, and detailed column information for LLM analysis"

    async def execute(
        self, data: pd.DataFrame, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            # Basic statistics
            basic_stats = {
                "rows": data.shape[0],
                "columns": data.shape[1],
                "data_types": data.dtypes.astype(str).to_dict(),
                "missing_values": data.isnull().sum().to_dict(),
            }

            # Identify metrics (row labels from first non-numeric column)
            metrics = []
            metric_column = None
            for col in data.columns:
                if data[col].dtype not in ["float64", "int64"]:
                    metric_column = col
                    # Get unique non-null values as metrics
                    metrics = data[col].dropna().unique().tolist()
                    break

            # Identify periods (numeric column names)
            periods = []
            for col in data.columns:
                if data[col].dtype in ["float64", "int64"]:
                    periods.append(col)

            # Sort periods chronologically
            periods_sorted = sorted(periods)

            # Detailed column information
            columns_info = []
            for col in data.columns:
                col_info = {
                    "name": col,
                    "dtype": str(data[col].dtype),
                    "null_count": int(data[col].isnull().sum()),
                    "unique_count": int(data[col].nunique()),
                }

                if data[col].dtype in ["float64", "int64"]:
                    # Numeric column statistics
                    col_info.update(
                        {
                            "min": (
                                float(data[col].min()) if not data[col].empty else None
                            ),
                            "max": (
                                float(data[col].max()) if not data[col].empty else None
                            ),
                            "mean": (
                                float(data[col].mean()) if not data[col].empty else None
                            ),
                        }
                    )
                else:
                    # Non-numeric column sample values
                    sample_values = data[col].dropna().head(3).tolist()
                    col_info["sample_values"] = sample_values

                columns_info.append(col_info)

            # Sample data (first 3 rows)
            sample_data = data.head(3).to_dict("records")

            # Create the complete profile
            profile = {
                "basic_stats": basic_stats,
                "periods": periods_sorted,
                "metrics": metrics,
                "columns": columns_info,
                "sample_data": sample_data,
            }

            return {
                "success": True,
                "profile": profile,
                "message": f"Data profile created successfully. Found {len(metrics)} metrics and {len(periods)} periods.",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create data profile: {str(e)}",
            }
