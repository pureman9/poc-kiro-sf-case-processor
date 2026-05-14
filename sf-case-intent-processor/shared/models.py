"""Shared data models used across all pipeline components."""

from dataclasses import dataclass, field
from enum import Enum


class ProcessingStatus(Enum):
    """Outcome status for a processed case."""
    COMPLETED = "COMPLETED"   # Case fully processed, customer record updated
    SKIPPED   = "SKIPPED"     # Case not processed — missing intent, unrecognized intent, or validation failure
    FAILED    = "FAILED"      # Unexpected error during processing


@dataclass
class ProcessingResult:
    """Captures the outcome of processing a single case through the pipeline."""
    case_id: str
    status: ProcessingStatus
    reason: str | None = None
    field_updated: str | None = None
    cid: str | None = None
    mobius_synced: bool = False


@dataclass
class ValidationResult:
    """Captures the outcome of a validation step."""
    ok: bool
    reason: str | None = None
    doc_id: str | None = None
