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
            trends = []
            numeric_columns = data.select_dtypes(include=["number"]).columns

            for col in numeric_columns:
                if len(data) >= 2:
                    # Simple trend analysis - compare first and last values
                    first_value = data[col].iloc[0]
                    last_value = data[col].iloc[-1]
                    change = last_value - first_value
                    change_pct = (change / first_value * 100) if first_value != 0 else 0

                    trend = (
                        "increasing"
                        if change > 0
                        else "decreasing" if change < 0 else "stable"
                    )

                    trends.append(
                        {
                            "metric": col,
                            "first_value": round(first_value, 2),
                            "last_value": round(last_value, 2),
                            "change": round(change, 2),
                            "change_percentage": round(change_pct, 2),
                            "trend": trend,
                        }
                    )

            return {
                "success": True,
                "results": trends,
                "message": "Trend analysis completed",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to perform trend analysis: {str(e)}",
            }
