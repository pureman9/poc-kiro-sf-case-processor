"""Models for the Document Validator module."""

from dataclasses import dataclass


@dataclass
class DocumentValidationResult:
    """Result of document validation for a case."""
    ok: bool
    reason: str | None = None
    doc_id: str | None = None
