import pandas as pd
from typing import Dict, Any
from .base import AnalysisTool


class TrendAnalyzer(AnalysisTool):
    @property
    def name(self) -> str:
        return "trend_analyzer"

    @property
    def description(self) -> str:
        return "Analyzes trends in the data"

    async def execute(
        self, data: pd.DataFrame, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            metric = parameters.get("metric")
            periods = parameters.get("periods", [])

            if not metric:
                return {
                    "success": False,
                    "error": "No metric specified",
                    "message": "Please specify a metric to analyze",
                }

            # Find the metric row - look in the first column (usually unnamed:_0 or similar)
            metric_column = data.columns[0]  # First column contains metric names

            # Find the row that contains the metric (case-insensitive)
            metric_row = None
            for idx, row_value in enumerate(data[metric_column]):
                if (
                    pd.notna(row_value)
                    and str(row_value).lower().strip() == metric.lower().strip()
                ):
                    metric_row = idx
                    break

            if metric_row is None:
                # Try partial matching if exact match fails
                for idx, row_value in enumerate(data[metric_column]):
                    if pd.notna(row_value) and metric.lower() in str(row_value).lower():
                        metric_row = idx
                        break

            if metric_row is None:
                return {
                    "success": False,
                    "error": f"Metric '{metric}' not found",
                    "message": f"Could not find metric '{metric}' in the data. Available metrics: {list(data[metric_column].dropna())}",
                }

            # Get the data for this metric across time periods
            metric_data = data.iloc[metric_row]
            numeric_columns = data.select_dtypes(include=["number"]).columns

            if len(numeric_columns) < 2:
                return {
                    "success": False,
                    "error": "Insufficient data",
                    "message": "Need at least 2 time periods for trend analysis",
                }

            # Create trend analysis for the specific metric across time periods
            values = []
            for col in numeric_columns:
                values.append(
                    {
                        "period": col,
                        "value": (
                            round(metric_data[col], 2)
                            if pd.notna(metric_data[col])
                            else 0
                        ),
                    }
                )

            # Calculate overall trend
            first_value = values[0]["value"]
            last_value = values[-1]["value"]
            total_change = last_value - first_value
            total_change_pct = (
                (total_change / first_value * 100) if first_value != 0 else 0
            )

            overall_trend = (
                "increasing"
                if total_change > 0
                else "decreasing" if total_change < 0 else "stable"
            )

            # Calculate period-over-period changes
            period_changes = []
            for i in range(1, len(values)):
                prev_value = values[i - 1]["value"]
                curr_value = values[i]["value"]
                change = curr_value - prev_value
                change_pct = (change / prev_value * 100) if prev_value != 0 else 0

                period_changes.append(
                    {
                        "from_period": values[i - 1]["period"],
                        "to_period": values[i]["period"],
                        "from_value": prev_value,
                        "to_value": curr_value,
                        "change": round(change, 2),
                        "change_percentage": round(change_pct, 2),
                        "trend": (
                            "increasing"
                            if change > 0
                            else "decreasing" if change < 0 else "stable"
                        ),
                    }
                )

            return {
                "success": True,
                "metric": metric,
                "values": values,
                "period_changes": period_changes,
                "overall_trend": {
                    "first_value": round(first_value, 2),
                    "last_value": round(last_value, 2),
                    "total_change": round(total_change, 2),
                    "total_change_percentage": round(total_change_pct, 2),
                    "trend": overall_trend,
                },
                "message": f"Trend analysis completed for {metric}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to perform trend analysis: {str(e)}",
            }
