"""Models for the Customer Data Store module."""

from dataclasses import dataclass


@dataclass
class UpdateResult:
    """Result of a customer record update operation."""
    ok: bool
    reason: str | None = None
    cid: str | None = None
    field_updated: str | None = None
