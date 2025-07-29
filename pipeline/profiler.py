"""Advanced profiling step with optional external engines.

If `config.profiler.mode` is:
            # Convert to JSON-serializable format
            sample_data_raw = df.head(3).to_dict("records")
            sample_data = [{str(k): v for k, v in record.items()} for record in sample_data_raw]

            return ProfileJSON(
                basic_stats=basic,
                periods=[],
                metrics=[],
                columns=[],
                sample_data=sample_data,
            )builtin": use pandas to compute stats, correlations, distributions.
    - "ydata": attempt to run ydata-profiling (fallback to builtin if import fails).
    - "capitalone": attempt DataProfiler; fallback to builtin.
    - "none": return minimal profile.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Any

import numpy as np
import pandas as pd

from .audit import AuditLogger
from .schemas import PipelineConfig, ProfileJSON

ProfilerStepVersion = "0.1.0"


# ---------------------------------------------------------------------------
# Built-in profiler functions
# ---------------------------------------------------------------------------


def _basic_stats(df: pd.DataFrame) -> Dict[str, any]:  # type: ignore  # noqa: ANN401
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "data_types": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
    }


def _correlations(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    num_df = df.select_dtypes(include=[np.number])
    if num_df.shape[1] < 2:
        return {}
    corr = num_df.corr().fillna(0)
    # Convert to proper type
    return {
        str(k): {str(k2): float(v2) for k2, v2 in v.items()}
        for k, v in corr.to_dict().items()
    }


def _value_distributions(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    dists: Dict[str, Dict[str, Any]] = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            # Filter out NaN values for statistics
            non_null_values = df[col].dropna()
            if len(non_null_values) > 0:
                dists[col] = {
                    "min": float(non_null_values.min()),
                    "q1": float(non_null_values.quantile(0.25)),
                    "median": float(non_null_values.median()),
                    "q3": float(non_null_values.quantile(0.75)),
                    "max": float(non_null_values.max()),
                }
            else:
                dists[col] = {"note": "All values are null"}
        else:
            top_counts = Counter(df[col].dropna()).most_common(3)
            dists[col] = {"top_values": top_counts}
    return dists


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def profile_dataframe(
    df: pd.DataFrame, cfg: PipelineConfig, audit: AuditLogger
) -> ProfileJSON:  # noqa: D401
    mode = cfg.profiler.mode

    if mode == "none":
        audit.log(
            step="profiler",
            action="skip",
            rows_affected=0,
            step_version=ProfilerStepVersion,
        )
        return ProfileJSON(
            basic_stats={}, periods=[], metrics=[], columns=[], sample_data=[]
        )

    # -------------------------------------------------------------------
    # Choose engine
    # -------------------------------------------------------------------
    if mode == "ydata":
        try:
            from ydata_profiling import ProfileReport  # type: ignore

            pr = ProfileReport(
                df, minimal=True, correlations={"pearson": {"calculate": True}}
            )
            audit.log(
                step="profiler",
                action="ydata_profile",
                rows_affected=len(df),
                step_version=ProfilerStepVersion,
            )
            # Convert to JSON; ydata returns dict via to_json
            report_json = pr.to_json()
            # Placeholder mapping; we wrap full report
            return ProfileJSON(
                basic_stats=_basic_stats(df),
                periods=[],
                metrics=[],
                columns=[],
                sample_data=df.head(3).to_dict("records"),
            )
        except ImportError:  # fallback
            audit.log(
                step="profiler",
                action="ydata_not_installed",
                rows_affected=0,
                step_version=ProfilerStepVersion,
            )

    # builtin or fallback
    audit.log(
        step="profiler",
        action="builtin_profile",
        rows_affected=len(df),
        step_version=ProfilerStepVersion,
    )
    basic = _basic_stats(df)
    corr = _correlations(df)
    dist = _value_distributions(df)

    columns_info: List[Dict[str, any]] = []  # type: ignore  # noqa: ANN401
    for col in df.columns:
        columns_info.append(
            {
                "name": col,
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique()),
                "distribution": dist.get(col, {}),
            }
        )

    return ProfileJSON(
        basic_stats=basic,
        periods=[],
        metrics=[],
        columns=columns_info,
        sample_data=[
            {str(k): v for k, v in record.items()}
            for record in df.head(3).to_dict("records")
        ],
    )
