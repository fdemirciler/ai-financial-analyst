"""Pydantic schemas for pipeline I/O, configuration, and audit trail.
Keeping these lightweight enables runtime validation while remaining
JSON-serialisable for the orchestrator and LLM."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, validator

# ---------------------------------------------------------------------------
# Configuration Schemas
# ---------------------------------------------------------------------------

MissingStrategy = Literal["mean", "median", "zero", "drop", "ffill", "none"]
ProfilerMode = Literal["builtin", "ydata", "capitalone", "none"]


class CleanerConfig(BaseModel):
    """Config options controlling the cleaning behaviour."""

    missing_numeric: MissingStrategy = Field("median", description="Fill strategy for numeric")
    missing_text: MissingStrategy = Field("drop", description="Fill strategy for text/categorical")
    currency_symbols: List[str] = Field(default_factory=lambda: ["$", "€", "£"])


class ProfilerConfig(BaseModel):
    mode: ProfilerMode = Field("builtin", description="Profiler engine to use")
    correlation: bool = True


class ReaderConfig(BaseModel):
    max_size_mb: int = 50


class PipelineConfig(BaseModel):
    reader: ReaderConfig = Field(default_factory=ReaderConfig)
    cleaner: CleanerConfig = Field(default_factory=CleanerConfig)
    profiler: ProfilerConfig = Field(default_factory=ProfilerConfig)


# ---------------------------------------------------------------------------
# Audit Trail Schemas
# ---------------------------------------------------------------------------

class AuditEntry(BaseModel):
    step: str
    action: str
    column: Optional[str] = None
    rows_affected: Optional[int] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    step_version: Optional[str] = None


class AuditTrail(BaseModel):
    pipeline_version: str
    entries: List[AuditEntry]


# ---------------------------------------------------------------------------
# Data Schemas
# ---------------------------------------------------------------------------

class SheetMeta(BaseModel):
    source_path: str
    sheet: str
    nrows: int
    ncols: int


class LongRow(BaseModel):
    metric: Any
    period: Any  
    value: Any
    extras: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Output Schema
# ---------------------------------------------------------------------------

class ProfileJSON(BaseModel):
    basic_stats: Dict[str, Any]
    periods: List[Any]
    metrics: List[Any]
    columns: List[Dict[str, Any]]
    sample_data: List[Dict[str, Any]]


class PipelineResult(BaseModel):
    sheet: str
    meta: SheetMeta
    clean_data: List[LongRow]
    profile: ProfileJSON
    audit: AuditTrail
