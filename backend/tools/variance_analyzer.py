import pandas as pd
from typing import Dict, Any
from .base import AnalysisTool


class VarianceAnalyzer(AnalysisTool):
    @property
    def name(self) -> str:
        return "variance_analyzer"

    @property
    def description(self) -> str:
        return "Performs variance analysis between periods"

    async def execute(
        self, data: pd.DataFrame, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            # Identify numeric columns for analysis
            numeric_columns = data.select_dtypes(include=["number"]).columns

            # If specific periods are provided, use them. Otherwise, use the last two numeric columns as periods.
            period1_col = parameters.get("period1")
            period2_col = parameters.get("period2")

            if not period1_col or not period2_col:
                if len(numeric_columns) >= 2:
                    period1_col = numeric_columns[-2]
                    period2_col = numeric_columns[-1]
                else:
                    return {
                        "success": False,
                        "message": "Not enough numeric columns to compare for variance analysis.",
                        "data": None,
                    }

            if period1_col not in data.columns or period2_col not in data.columns:
                return {
                    "success": False,
                    "message": f"Specified period columns ('{period1_col}', '{period2_col}') not found in data.",
                    "data": None,
                }

            # Identify the first non-numeric column to use as the index/metric (typically financial statement line items)
            metric_column = None
            for col in data.columns:
                if data[col].dtype not in ["float64", "int64"]:
                    metric_column = col
                    break

            # Calculate variance
            variance_data = data.copy()
            variance_data["variance"] = (
                variance_data[period2_col] - variance_data[period1_col]
            )

            # Calculate percentage change, handle division by zero
            variance_data["variance_percentage"] = (
                variance_data["variance"] / variance_data[period1_col].abs()
            ) * 100

            # Always include the metric column if found (essential for financial statement analysis)
            if metric_column:
                # Column order: metric, period1, period2, variance, variance_percentage
                result_df = variance_data[
                    [
                        metric_column,
                        period1_col,
                        period2_col,
                        "variance",
                        "variance_percentage",
                    ]
                ]

                # Rename unnamed columns to user-friendly "Metrics" for better display
                display_metric_name = metric_column
                if metric_column.lower().startswith("unnamed"):
                    display_metric_name = "Metrics"
                    result_df = result_df.rename(
                        columns={metric_column: display_metric_name}
                    )

            else:
                # Column order: period1, period2, variance, variance_percentage
                result_df = variance_data[
                    [period1_col, period2_col, "variance", "variance_percentage"]
                ]

            # Prepare results with explicit column ordering
            results = {
                "success": True,
                "message": f"Variance analysis between {period1_col} and {period2_col} completed.",
                "data": result_df.to_dict(orient="records"),
                "periods_analyzed": {"period1": period1_col, "period2": period2_col},
                "metric_column": metric_column,
                "column_order": list(
                    result_df.columns
                ),  # Explicit column order for frontend
            }

            return results
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to perform variance analysis: {str(e)}",
                "data": None,
            }
