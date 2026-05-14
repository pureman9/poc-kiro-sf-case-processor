# Data Model

## Overview
**Storage**: Local JSON file (`customer_data.json`) for CustomerRecord. In-memory dataclasses for pipeline processing objects.
**ORM/Client**: Python `dataclasses` + `json` stdlib. No ORM — direct file I/O with `filelock`.

The data model has two layers:
1. **Pipeline objects** — in-memory dataclasses used during processing (SFCase, VerificationDocument, ProcessingResult, ValidationResult)
2. **Persistent storage** — CustomerRecord persisted to `customer_data.json`

---

## Entities

### SFCase

**Purpose**: Represents a single Salesforce case record retrieved by the extractor.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| case_id | str | Yes | Non-empty | Salesforce Case ID (e.g., "5001000000D8cuI") |
| cid | str | Yes | Non-empty | Customer ID — lookup key for CustomerDataStore |
| intent_name | str | Yes | Non-empty | Full intent name string from Salesforce (e.g., "ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล") |
| status | str | Yes | != "Closed" | Salesforce case status |
| new_value | str | No | — | The new value to apply (e.g., new first name). May be None if not present in case data |
| verification_documents | list[VerificationDocument] | Yes | Can be empty list | Documents attached to the case |

**Business Rules**:
1. `intent_name` must be non-empty and non-whitespace to be processable
2. `status` is guaranteed != "Closed" by the SOQL query filter
3. `cid` must match a key in CustomerDataStore for the update to succeed

**Python Dataclass**:
```python
@dataclass
class SFCase:
    case_id: str
    cid: str
    intent_name: str
    status: str
    new_value: str | None
    verification_documents: list[VerificationDocument]
```

---

### VerificationDocument

**Purpose**: Represents a document attached to a Salesforce case as proof for a customer request.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| doc_id | str | Yes | Non-empty | Document identifier (Salesforce attachment ID or custom field) |
| status | str | Yes | Non-empty | Document status value (e.g., "OK", "valid", "PENDING", "REJECTED") |

**Business Rules**:
1. A document is considered valid if `status.lower() in {"ok", "valid"}`
2. At least one valid document is required for the case to proceed
3. If multiple documents exist, the case is valid if ANY one has a valid status

**Python Dataclass**:
```python
@dataclass
class VerificationDocument:
    doc_id: str
    status: str

    def is_valid(self) -> bool:
        return self.status.strip().lower() in {"ok", "valid"}
```

---

### CustomerRecord

**Purpose**: A customer's data record stored in `customer_data.json`, keyed by CID.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| cid | str | Yes | PK (JSON key) | Customer ID — the JSON object key |
| first_name | str | No | — | Customer's first name |
| title | str | No | — | Customer's title/prefix (e.g., "Mr.", "Ms.", "นาย", "นาง") |
| last_name | str | No | — | Customer's last name |
| [other_fields] | any | No | — | Any additional fields — preserved unchanged on update |

**Business Rules**:
1. Only the field specified by the intent is updated — all other fields are preserved
2. CID must already exist in the store — no auto-creation of new records
3. Updates are atomic (file lock acquired before read-modify-write)

**JSON Storage Format**:
```json
{
  "C001234": {
    "cid": "C001234",
    "first_name": "สมชาย",
    "title": "นาย",
    "last_name": "ใจดี"
  },
  "C005678": {
    "cid": "C005678",
    "first_name": "สมหญิง",
    "title": "นาง",
    "last_name": "รักดี"
  }
}
```

**Updatable Fields by Intent**:
| Intent Sub-Type | Field Updated |
|---|---|
| เปลี่ยนแปลงชื่อ (first name change) | `first_name` |
| เปลี่ยนแปลงนามสกุล (last name change) | `last_name` |
| เปลี่ยนแปลงคำนำหน้า (title change) | `title` |

---

### ProcessingResult

**Purpose**: Captures the outcome of processing a single case through the pipeline.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| case_id | str | Yes | The Salesforce case ID |
| status | ProcessingStatus | Yes | COMPLETED, SKIPPED, or FAILED |
| reason | str | No | Human-readable reason for SKIPPED or FAILED |
| field_updated | str | No | Field name that was updated (COMPLETED only) |
| cid | str | No | CID of the customer record updated |

**ProcessingStatus Enum**:
```python
class ProcessingStatus(Enum):
    COMPLETED = "COMPLETED"   # Case fully processed, customer record updated
    SKIPPED   = "SKIPPED"     # Case not processed — missing intent, unrecognized intent, or validation failure
    FAILED    = "FAILED"      # Unexpected error during processing
```

---

### ValidationResult

**Purpose**: Captures the outcome of a validation step (document validation or intent validation).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ok | bool | Yes | True if validation passed |
| reason | str | No | Reason for failure (if ok=False) |
| doc_id | str | No | Document ID involved in failure (if applicable) |

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────┐
│                  IN-MEMORY (pipeline)                │
│                                                      │
│  ┌──────────────┐    1:N    ┌──────────────────────┐ │
│  │   SFCase     │──────────>│ VerificationDocument │ │
│  ├──────────────┤           ├──────────────────────┤ │
│  │ case_id (PK) │           │ doc_id               │ │
│  │ cid          │           │ status               │ │
│  │ intent_name  │           └──────────────────────┘ │
│  │ status       │                                     │
│  │ new_value    │    1:1    ┌──────────────────────┐ │
│  └──────────────┘──────────>│  ProcessingResult    │ │
│                             ├──────────────────────┤ │
│                             │ case_id              │ │
│                             │ status (enum)        │ │
│                             │ reason               │ │
│                             │ field_updated        │ │
│                             └──────────────────────┘ │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│              PERSISTENT (customer_data.json)         │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  CustomerRecord (keyed by CID)               │   │
│  ├──────────────────────────────────────────────┤   │
│  │  cid (PK / JSON key)                         │   │
│  │  first_name                                  │   │
│  │  title                                       │   │
│  │  last_name                                   │   │
│  │  [other fields — preserved on update]        │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘

SFCase.cid ──────────────────────────────> CustomerRecord.cid (lookup key)
```

---

## Data Access Patterns

| Query | Frequency | Method |
|-------|-----------|--------|
| Fetch all non-closed CIU cases from Salesforce | Once per pipeline run | SOQL via `simple_salesforce` |
| Look up CustomerRecord by CID | Once per case | Dict key lookup in loaded JSON |
| Update single field in CustomerRecord | Once per successfully validated case | Read-modify-write with filelock |
