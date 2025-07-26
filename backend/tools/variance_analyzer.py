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
            # This is a simplified variance analysis
            # In a real implementation, you'd want more sophisticated period detection
            variance_results = []

            # For demonstration, let's assume we're comparing first half vs second half
            if len(data) >= 2:
                midpoint = len(data) // 2
                period1 = data.iloc[:midpoint]
                period2 = data.iloc[midpoint:]

                numeric_columns = data.select_dtypes(include=["number"]).columns

                for col in numeric_columns:
                    if col in period1.columns and col in period2.columns:
                        mean1 = period1[col].mean() if len(period1) > 0 else 0
                        mean2 = period2[col].mean() if len(period2) > 0 else 0
                        variance = mean2 - mean1
                        variance_pct = (variance / mean1 * 100) if mean1 != 0 else 0

                        variance_results.append(
                            {
                                "metric": col,
                                "period1_average": round(mean1, 2),
                                "period2_average": round(mean2, 2),
                                "variance": round(variance, 2),
                                "variance_percentage": round(variance_pct, 2),
                            }
                        )

            return {
                "success": True,
                "results": variance_results,
                "message": "Variance analysis completed",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to perform variance analysis: {str(e)}",
            }
