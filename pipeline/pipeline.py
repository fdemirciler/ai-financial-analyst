"""High-level Pipeline orchestrator.

Usage example::

    from pipeline import Pipeline, PIPELINE_VERSION

    pipe = Pipeline()
    results = pipe.run_from_excel("/path/to/file.xlsx")

    for res in results:
        print(res.json())
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from .audit import AuditLogger
from .layout import detect_layout, identify_metric_period, to_long
from .reader import CSVReader, ExcelReader, DataSheet
from .schemas import PipelineConfig, PipelineResult, ProfileJSON
from .type_inferencer import TypeInferencer

# ---------------------------------------------------------------------------
# Import real cleaner implementation
# ---------------------------------------------------------------------------

from .cleaner import clean_dataframe  # noqa: E402


from .profiler import profile_dataframe  # noqa: E402

# ---------------------------------------------------------------------------
# Pipeline class
# ---------------------------------------------------------------------------


class Pipeline:
    """Run the end-to-end data processing flow on given files."""

    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()

    # ------------------------------------------------------------------
    # Public API helpers
    # ------------------------------------------------------------------

    def run_from_excel(self, path: str | Path) -> List[PipelineResult]:  # noqa: D401
        reader = ExcelReader(path, config=self.config.reader)
        return self._run(reader.read())

    def run_from_csv(self, path: str | Path) -> List[PipelineResult]:  # noqa: D401
        reader = CSVReader(path, config=self.config.reader)
        return self._run(reader.read())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run(self, sheets: List[DataSheet]) -> List[PipelineResult]:
        results: List[PipelineResult] = []

        for sheet_name, df, meta in sheets:
            audit = AuditLogger()

            # Type inference
            type_info = TypeInferencer.infer(df)
            audit.log(step="type_inferencer", action="infer", rows_affected=len(df), details={"columns": list(type_info.keys())}, step_version=TypeInferencer.VERSION)

            # Layout detection & normalisation
            layout = detect_layout(df)
            layout_info = identify_metric_period(df, layout)
            audit.log(step="layout", action="detect", details=layout_info)
            df_long = to_long(df, layout_info, audit=audit)

            # Cleaning
            df_clean = clean_dataframe(df_long, self.config.cleaner, audit)
            # Profiling
            profile = profile_dataframe(df_clean, self.config, audit)
            # Build result
            raw_records = df_clean.to_dict("records")
            clean_records = []
            for rec in raw_records:
                clean_records.append(
                    {
                        "metric": rec.get("metric"),
                        "period": (
                        str(rec.get("period")) if isinstance(rec.get("period"), str)
                        else str(rec.get("period").date()) if hasattr(rec.get("period"), "date")
                        else str(rec.get("period")) if rec.get("period") is not None
                        else None
                    ),
                        "value": float(rec.get("value")) if isinstance(rec.get("value"), (int, float)) or rec.get("value") is not None else rec.get("value"),
                        "extras": {k: v for k, v in rec.items() if k not in {"metric", "period", "value"}},
                    }
                )

            result = PipelineResult(
                sheet=sheet_name,
                meta=meta,
                clean_data=clean_records,  # type: ignore[arg-type]
                profile=profile,
                audit=audit.to_trail(),
            )
            results.append(result)

        return results
