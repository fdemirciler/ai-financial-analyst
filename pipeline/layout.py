"""Layout detection and normalisation helpers.

This module figures out whether a dataframe is in *wide* or *long* format with
respect to financial statements (metrics vs periods) and provides a
`to_long` function to guarantee a unified long representation.
"""

from __future__ import annotations

import re
from typing import Dict, List

import pandas as pd
from pandas.api.types import is_numeric_dtype

from .audit import AuditLogger

# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

def _looks_like_period(col: str) -> bool:  # noqa: D401
    """Return True if column header looks like a period (year, quarter, month)."""
    pattern = re.compile(r"^(19|20)\d{2}([-_/]?Q[1-4])?$", re.IGNORECASE)
    return bool(pattern.match(str(col)))


def detect_layout(df: pd.DataFrame) -> str:
    """Detect *wide*, *long*, or *unknown* layout."""
    period_like = [c for c in df.columns if _looks_like_period(str(c))]
    if len(period_like) >= 2:
        return "wide"

    # long layout often has a date column convertible to datetime
    sample_cols = df.sample(min(len(df), 100)).columns if len(df) > 100 else df.columns
    for col in sample_cols:
        if pd.to_datetime(df[col], errors="coerce").notna().sum() / len(df) > 0.2:
            return "long"

    return "unknown"


def identify_metric_period(df: pd.DataFrame, layout: str | None = None) -> Dict[str, any]:  # type: ignore  # noqa: ANN401
    """Return structured metric/period info required for normalisation."""
    layout = layout or detect_layout(df)

    metric_column: str | None = None
    period_columns: List[str] = []

    if layout == "wide":
        for col in df.columns:
            if _looks_like_period(str(col)):
                period_columns.append(str(col))
        # choose first non-numeric column as metric col fallback
        metric_column = next((c for c in df.columns if not is_numeric_dtype(df[c])), None)
    elif layout == "long":
        # assume there is a date column convertible to datetime
        date_cols = [c for c in df.columns if pd.to_datetime(df[c], errors="coerce").notna().sum()]
        if date_cols:
            period_columns = date_cols  # one or more
        metric_column = next((c for c in df.columns if c not in period_columns), None)

    # Fallback: if metric_column still None, pick first column not in period_columns
    if metric_column is None and df.columns.any():
        metric_column = next((c for c in df.columns if c not in period_columns), str(df.columns[0]))

    return {
        "layout": layout,
        "metric_column": metric_column,
        "period_columns": period_columns,
    }


# ---------------------------------------------------------------------------
# Normalisation helper
# ---------------------------------------------------------------------------

def to_long(df: pd.DataFrame, layout_info: Dict[str, any], audit: AuditLogger | None = None) -> pd.DataFrame:  # noqa: ANN401
    """Return a long-format dataframe with columns [metric, period, value, *extras]."""
    layout = layout_info.get("layout")
    metric = layout_info.get("metric_column") or "metric"

    if layout == "wide":
        value_vars = layout_info.get("period_columns", [])
        long_df = df.melt(id_vars=[metric], value_vars=value_vars, var_name="period", value_name="value")
        # Standardise column names
        long_df.rename(columns={metric: "metric"}, inplace=True)
        if audit:
            audit.log(step="normaliser", action="melt_wide", rows_affected=len(long_df), details={"period_cols": value_vars})
    elif layout == "long":
        long_df = df.copy()
        # Ensure canonical column names
        if metric in long_df.columns and metric != "metric":
            long_df.rename(columns={metric: "metric"}, inplace=True)
        if audit:
            audit.log(step="normaliser", action="pass_through_long", rows_affected=len(long_df))
    else:
        long_df = df.copy()
        if metric in long_df.columns and metric != "metric":
            long_df.rename(columns={metric: "metric"}, inplace=True)
        if audit:
            audit.log(step="normaliser", action="unknown_layout", rows_affected=len(long_df))

    return long_df
