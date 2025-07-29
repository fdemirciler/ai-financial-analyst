"""File readers supporting multi-sheet Excel, CSV, and Parquet.

Each reader returns a list of `(sheet_name, df, meta)` tuples to keep a common
interface for downstream pipeline steps.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import pandas as pd

from .schemas import SheetMeta, ReaderConfig

DataSheet = Tuple[str, pd.DataFrame, SheetMeta]


class ExcelReader:
    """Read Excel files with support for multi-sheet workflows."""

    def __init__(self, path: str | Path, config: ReaderConfig | None = None):
        self.path = Path(path)
        self.config = config or ReaderConfig()

        if self.path.stat().st_size > self.config.max_size_mb * 1_048_576:
            raise ValueError(f"File {self.path} exceeds {self.config.max_size_mb} MB limit.")

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def read(self) -> List[DataSheet]:
        """Return list of sheets."""
        xls = pd.ExcelFile(self.path, engine="openpyxl")
        results: List[DataSheet] = []

        for sheet_name in xls.sheet_names:
            df = xls.parse(sheet_name, dtype_backend="pyarrow")
            meta = SheetMeta(
                source_path=str(self.path),
                sheet=sheet_name,
                nrows=len(df),
                ncols=len(df.columns),
            )
            results.append((sheet_name, df, meta))
        return results


class CSVReader:
    """Read CSV files (single-sheet interface)."""

    def __init__(self, path: str | Path, config: ReaderConfig | None = None):
        self.path = Path(path)
        self.config = config or ReaderConfig()

    def read(self) -> List[DataSheet]:  # noqa: D401
        df = pd.read_csv(self.path, dtype_backend="pyarrow")
        meta = SheetMeta(
            source_path=str(self.path),
            sheet=self.path.stem,
            nrows=len(df),
            ncols=len(df.columns),
        )
        return [(self.path.stem, df, meta)]
