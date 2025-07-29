"""Lightweight audit logger used across pipeline steps.
Keeps an ordered list of `AuditEntry` objects and can serialise back to
`AuditTrail` defined in `schemas.py`."""

from __future__ import annotations

from datetime import datetime
from typing import List

from .schemas import AuditEntry, AuditTrail

PIPELINE_VERSION = "0.1.0"  # Define locally to avoid circular import


class AuditLogger:
    """Collects audit entries during a pipeline run."""

    __slots__ = ("_entries",)

    def __init__(self) -> None:
        self._entries: List[AuditEntry] = []

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------

    def log(
        self,
        step: str,
        action: str,
        column: str | None = None,
        rows_affected: int | None = None,
        details: dict | None = None,
        step_version: str | None = None,
    ) -> None:
        """Append an `AuditEntry`."""
        self._entries.append(
            AuditEntry(
                step=step,
                action=action,
                column=column,
                rows_affected=rows_affected,
                details=details or {},
                timestamp=datetime.utcnow(),
                step_version=step_version,
            )
        )

    # ------------------------------------------------------------------
    # Conversion helpers
    # ------------------------------------------------------------------

    def to_trail(self) -> AuditTrail:
        """Convert to a serialisable `AuditTrail`."""
        return AuditTrail(
            pipeline_version=PIPELINE_VERSION, entries=self._entries.copy()
        )
