"""Data models for Salesforce case extraction."""

from dataclasses import dataclass, field


@dataclass
class VerificationDocument:
    """Represents a document attached to a Salesforce case as proof for a customer request."""
    doc_id: str
    status: str

    def __post_init__(self):
        if not self.doc_id or not self.doc_id.strip():
            raise ValueError("doc_id must be a non-empty string")
        if not self.status or not self.status.strip():
            raise ValueError("status must be a non-empty string")

    def is_valid(self) -> bool:
        """Check if document status is acceptable ('OK' or 'valid', case-insensitive)."""
        return self.status.strip().lower() in {"ok", "valid"}


@dataclass
class SFCase:
    """Represents a single Salesforce case record retrieved by the extractor."""
    case_id: str
    cid: str
    intent_name: str
    status: str
    new_value: str | None = None
    verification_documents: list[VerificationDocument] = field(default_factory=list)

    def __post_init__(self):
        if not self.case_id or not self.case_id.strip():
            raise ValueError("case_id must be a non-empty string")
        if not self.cid or not self.cid.strip():
            raise ValueError("cid must be a non-empty string")
