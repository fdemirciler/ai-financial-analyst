"""Unified column type inference utility.
Currently a scaffold — real heuristics will be implemented incrementally.

The public contract is:
    TypeInferencer.infer(df) -> Dict[str, ColumnTypeInfo]
where `ColumnTypeInfo` is a dataclass-like dict:
    {
      "column_type": "currency|percentage|date|numeric|id|text",
      "confidence": float,
      "notes": str,
      "recommended_actions": List[str]
    }
"""

from __future__ import annotations

from typing import Dict, List

import pandas as pd

ColumnType = str
ColumnTypeInfo = Dict[str, str | float | List[str]]


class TypeInferencer:  # pylint: disable=too-few-public-methods
    """Shared engine to detect semantic column types."""

    VERSION = "0.2.0"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def infer(df: pd.DataFrame) -> Dict[str, ColumnTypeInfo]:  # noqa: D401
        """Infer semantic column types with simple heuristics.

        Currently supports: currency, percentage, date, numeric, id, text, period.
        """
        info: Dict[str, ColumnTypeInfo] = {}

        for col in df.columns:
            series = df[col]
            col_type: ColumnType
            confidence: float = 0.0
            notes: str = ""
            rec: List[str] = []

            # 0. Period detection (year columns like 2022, 2023, etc.)
            # Check if column name looks like a year/period first
            col_str = str(col).strip()
            is_year_column = False

            # Check if column is numeric year (int or string)
            try:
                if isinstance(col, int) and 1900 <= col <= 2100:
                    is_year_column = True
                elif (
                    isinstance(col, float)
                    and col.is_integer()
                    and 1900 <= int(col) <= 2100
                ):
                    is_year_column = True
                elif col_str.isdigit() and 1900 <= int(col_str) <= 2100:
                    is_year_column = True
            except (ValueError, TypeError):
                pass

            if is_year_column:
                col_type = "period"
                confidence = 1.0
                notes = f"Column name '{col_str}' appears to be a year/period"
                info[str(col)] = {
                    "column_type": col_type,
                    "confidence": confidence,
                    "notes": notes,
                    "recommended_actions": rec,
                }
                continue

            # 1. Percentage detection
            pct_mask = series.astype(str).str.endswith("%")
            if pct_mask.mean() > 0.5:
                col_type = "percentage"
                confidence = pct_mask.mean()
                info[str(col)] = {
                    "column_type": col_type,
                    "confidence": confidence,
                    "notes": notes,
                    "recommended_actions": rec,
                }
                continue

            # 2. Currency detection (symbol presence)
            cur_mask = series.astype(str).str.contains(r"[\$€£]", regex=True)
            if cur_mask.mean() > 0.3:
                col_type = "currency"
                confidence = cur_mask.mean()
                info[str(col)] = {
                    "column_type": col_type,
                    "confidence": confidence,
                    "notes": notes,
                    "recommended_actions": rec,
                }
                continue

            # 3. Date detection via parsing sample (but skip if column might be a period)
            # Skip date parsing for columns that look like years or have numeric-only values
            skip_date_detection = False
            try:
                # Skip if all values look like years
                if series.dtype in ["int64", "float64"] or (
                    series.astype(str).str.isdigit().all()
                    and series.astype(float).between(1900, 2100).all()
                ):
                    skip_date_detection = True
            except Exception:
                pass

            if not skip_date_detection:
                try:
                    parsed = pd.to_datetime(series, errors="coerce")
                    if parsed.notna().sum() / len(series) > 0.5:
                        col_type = "date"
                        confidence = parsed.notna().mean()
                        info[str(col)] = {
                            "column_type": col_type,
                            "confidence": confidence,
                            "notes": notes,
                            "recommended_actions": rec,
                        }
                        continue
                except Exception:
                    # Skip date detection if it fails
                    pass

            # 4. Numeric detection
            try:
                numeric_series = pd.to_numeric(series, errors="coerce")
                if numeric_series.notna().sum() / len(series) > 0.7:
                    col_type = "numeric"
                    confidence = numeric_series.notna().mean()
                    info[str(col)] = {
                        "column_type": col_type,
                        "confidence": confidence,
                        "notes": notes,
                        "recommended_actions": rec,
                    }
                    continue
            except Exception:
                # Skip numeric detection if it fails
                pass

            # 5. ID detection (unique string, high uniqueness)
            try:
                if series.dtype == "object" and series.nunique() / len(series) > 0.9:
                    col_type = "id"
                    confidence = 0.8
                else:
                    col_type = "text"
                    confidence = 0.5
            except Exception:
                col_type = "text"
                confidence = 0.3

            info[str(col)] = {
                "column_type": col_type,
                "confidence": confidence,
                "notes": notes,
                "recommended_actions": rec,
            }

        return info
