"""Data models for Salesforce case extraction — mapped to real sandbox schema."""

from dataclasses import dataclass, field


@dataclass
class VerificationDocument:
    """Represents a document attached to a Salesforce case (Attachment or ContentDocument)."""
    doc_id: str
    name: str
    content_type: str | None = None
    size_bytes: int = 0

    def __post_init__(self):
        if not self.doc_id or not self.doc_id.strip():
            raise ValueError("doc_id must be a non-empty string")
        if not self.name or not self.name.strip():
            raise ValueError("name must be a non-empty string")

    def is_valid(self) -> bool:
        """Check if document exists (non-zero size). In real flow, status check happens via OCR."""
        return self.size_bytes > 0


@dataclass
class SFCase:
    """Represents a single Salesforce case record — mapped to real sandbox fields.

    Field mapping (Salesforce → SFCase):
        Id              → case_id
        CaseNumber      → case_number
        Subject         → subject (full intent string: "ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล")
        Type__c         → intent_type (short: "CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล")
        Status          → status
        Sub_Status__c   → sub_status
        Category__c     → category
        Customer_Name__c → customer_name
        Process_Add_Info_1__c → new_first_name
        Process_Add_Info_2__c → new_last_name
        Process_Add_Info_3__c → new_title
        Process_Add_Info_4__c → old_name
        Process_Add_Info_9__c → citizen_id
        ContactId       → contact_id
        AccountId       → account_id
    """
    case_id: str
    case_number: str
    subject: str
    intent_type: str
    status: str
    sub_status: str | None = None
    category: str | None = None
    customer_name: str | None = None
    citizen_id: str | None = None
    new_first_name: str | None = None
    new_last_name: str | None = None
    new_title: str | None = None
    old_name: str | None = None
    contact_id: str | None = None
    account_id: str | None = None
    verification_documents: list[VerificationDocument] = field(default_factory=list)

    def __post_init__(self):
        if not self.case_id or not self.case_id.strip():
            raise ValueError("case_id must be a non-empty string")
        if not self.case_number or not self.case_number.strip():
            raise ValueError("case_number must be a non-empty string")

    @property
    def intent_name(self) -> str:
        """Return the intent type for routing (from Type__c field)."""
        return self.intent_type or ""

    @property
    def cid(self) -> str:
        """Return citizen ID as the customer identifier."""
        return self.citizen_id or ""
