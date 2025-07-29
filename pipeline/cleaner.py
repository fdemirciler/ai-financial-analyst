"""Config-driven data cleaning step.

Relies on `TypeInferencer` to decide per-column actions and applies missing-
value strategies defined in :class:`pipeline.schemas.CleanerConfig`.
"""

from __future__ import annotations

import re
from typing import Dict

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

from .audit import AuditLogger
from .schemas import CleanerConfig
from .type_inferencer import TypeInferencer

__all__ = ["clean_dataframe", "CleanerStepVersion"]

CleanerStepVersion = "0.0.1"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CURRENCY_RE = re.compile(r"[\$€£]")
_PERCENT_RE = re.compile(r"%$")
_NEG_PAREN_RE = re.compile(r"\(([^)]+)\)")


def _clean_currency(series: pd.Series) -> pd.Series:  # noqa: D401
    as_str = series.astype(str).str.replace(_NEG_PAREN_RE.pattern, r"-\1", regex=True)
    as_str = as_str.str.replace(_CURRENCY_RE.pattern, "", regex=True).str.replace(
        ",", ""
    )
    return pd.to_numeric(as_str, errors="coerce")


def _clean_percentage(series: pd.Series) -> pd.Series:  # noqa: D401
    cleaned = series.astype(str).str.replace("%", "").str.replace(",", "")
    numeric = pd.to_numeric(cleaned, errors="coerce")
    return numeric / 100.0


# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------


def clean_dataframe(
    df: pd.DataFrame, config: CleanerConfig, audit: AuditLogger
) -> pd.DataFrame:
    """Return a cleaned dataframe according to provided *config*."""
    df_out = df.copy()
    type_info: Dict[str, dict] = TypeInferencer.infer(df_out)

    for col, info in type_info.items():
        col_type = info["column_type"]
        if col_type == "currency":
            before_na = df_out[col].isna().sum()
            df_out[col] = _clean_currency(df_out[col])
            after_na = df_out[col].isna().sum()
            audit.log(
                step="cleaner",
                action="clean_currency",
                column=col,
                rows_affected=int(before_na - after_na),
                step_version=CleanerStepVersion,
            )
        elif col_type == "percentage":
            df_out[col] = _clean_percentage(df_out[col])
            audit.log(
                step="cleaner",
                action="clean_percentage",
                column=col,
                step_version=CleanerStepVersion,
            )
        elif col_type == "date":
            df_out[col] = pd.to_datetime(df_out[col], errors="coerce")
            audit.log(
                step="cleaner",
                action="parse_date",
                column=col,
                step_version=CleanerStepVersion,
            )
        elif col_type == "numeric":
            # ensure numeric dtype
            df_out[col] = pd.to_numeric(df_out[col], errors="coerce")

        # Missing value filling
        if is_numeric_dtype(df_out[col]):
            strategy = config.missing_numeric
            if strategy == "mean":
                df_out[col] = df_out[col].fillna(df_out[col].mean())
            elif strategy == "median":
                df_out[col] = df_out[col].fillna(df_out[col].median())
            elif strategy == "zero":
                df_out[col] = df_out[col].fillna(0)
            elif strategy == "drop":
                pass  # handled later
        else:
            if config.missing_text == "drop":
                pass  # drop later
            elif config.missing_text == "ffill":
                df_out[col] = df_out[col].ffill()
            elif config.missing_text == "none":
                df_out[col] = df_out[col].fillna("")

    # If drop strategy chosen, remove rows with any remaining NaNs
    if config.missing_numeric == "drop" or config.missing_text == "drop":
        before = len(df_out)
        df_out.dropna(inplace=True)
        audit.log(
            step="cleaner", action="drop_na_rows", rows_affected=before - len(df_out)
        )

    return df_out
