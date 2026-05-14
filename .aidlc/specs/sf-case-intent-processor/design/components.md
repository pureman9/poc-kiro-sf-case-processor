# Components

## Overview

The SF Case Intent Processor is a sequential pipeline with 5 components. The pipeline runner orchestrates execution: SFCaseExtractor fetches cases from Salesforce, IntentAnalyzer routes each case to the correct processor via IntentRegistry, and each registered processor (e.g., PersonalInfoChangeProcessor) runs its own DocumentValidator and CustomerDataStore operations.

All components are stateless except CustomerDataStore (which owns the JSON file). Each component logs its own outcomes. Per-case errors are isolated — one failure does not stop processing of other cases.

---

## SFCaseExtractor

**Purpose**: Query Salesforce for all non-closed Customer Information Update cases and return them as structured data.

**Technology**: Python, `simple_salesforce` library

**Responsibilities**:
- Build and execute a SOQL query filtering `Status != 'Closed'` AND intent name in the Customer Information Update category
- Retry the query up to 3 times on failure or timeout (30s)
- Return a list of `SFCase` objects
- Log zero-result and error conditions

**Exposes**:
- `extract() -> list[SFCase]` — executes the query and returns results; raises `ExtractionError` after 3 failed retries

**Consumes**:
- Salesforce REST API via `simple_salesforce.Salesforce` client
- Environment config: `SF_USERNAME`, `SF_PASSWORD`, `SF_SECURITY_TOKEN`, `SF_DOMAIN`

**Internal Structure**:
```
sf_case_extractor/
  ├── extractor.py        # SFCaseExtractor class
  ├── soql_builder.py     # Builds SOQL query string
  └── models.py           # SFCase dataclass
```

**Key Decisions**:
1. Dual-filter SOQL (status + intent category) at query time — reduces payload and enforces scope at source (Requirement 1, AC5)
2. Retry with fixed 2-second delay between attempts — simple and predictable for batch processing

**Error Handling**:
- `SalesforceAuthenticationFailed` → log and raise `ExtractionError` immediately (no retry — credentials issue)
- `SalesforceExpiredSession` → re-authenticate and retry
- Network timeout (>30s) → retry up to 3 times, then raise `ExtractionError`
- Empty result → return `[]`, log "0 cases found"

---

## IntentAnalyzer

**Purpose**: Extract the intent name from each case and route it to the correct registered processor.

**Technology**: Python

**Responsibilities**:
- Extract `intent_name` field from each `SFCase`
- Validate the intent name is non-empty and non-whitespace
- Look up the registered processor in `IntentRegistry`
- Dispatch the case to the matched processor
- Flag and log unprocessable cases (missing intent, unrecognized intent)

**Exposes**:
- `analyze(case: SFCase) -> ProcessingResult` — routes and processes a single case

**Consumes**:
- `IntentRegistry` — for processor lookup
- `SFCase` — input data

**Internal Structure**:
```
intent_analyzer/
  ├── analyzer.py         # IntentAnalyzer class
  └── exceptions.py       # MissingIntentError, UnrecognizedIntentError
```

**Key Decisions**:
1. Exact string match for intent name lookup — no fuzzy matching (Requirement 6, AC2)
2. Per-case try/except — one case failure does not halt the pipeline

**Error Handling**:
- Empty/whitespace intent name → log case ID + reason, return `ProcessingResult(status=SKIPPED, reason=MISSING_INTENT)`
- Unrecognized intent name → log case ID + intent name, return `ProcessingResult(status=SKIPPED, reason=UNRECOGNIZED_INTENT)`
- Processor raises exception → log case ID + exception, return `ProcessingResult(status=FAILED, reason=str(exception))`

---

## IntentRegistry

**Purpose**: Maintain the registry of intent name → processor mappings. Enforce registration rules.

**Technology**: Python

**Responsibilities**:
- Register intent processors with a unique intent name key
- Reject duplicate registrations (log conflict)
- Reject registrations missing validation rules or processing actions
- Look up processor by exact intent name

**Exposes**:
- `register(intent_name: str, processor: IntentProcessor) -> None` — registers a processor; raises `RegistrationError` on duplicate or invalid processor
- `get(intent_name: str) -> IntentProcessor | None` — returns processor or None if not found

**Consumes**:
- `IntentProcessor` — abstract base class that all processors must implement

**Internal Structure**:
```
intent_analyzer/
  ├── registry.py         # IntentRegistry class
  └── base_processor.py   # IntentProcessor ABC (validate + process methods)
```

**Key Decisions**:
1. `IntentProcessor` is an Abstract Base Class with `validate(case)` and `process(case)` abstract methods — enforces Requirement 6, AC3
2. Registration validation at registration time, not at call time — fail fast

**IntentProcessor Interface**:
```python
from abc import ABC, abstractmethod

class IntentProcessor(ABC):
    @abstractmethod
    def validate(self, case: SFCase) -> ValidationResult:
        """Run validation rules. Return ValidationResult(ok=True/False, reason=str)."""
        ...

    @abstractmethod
    def process(self, case: SFCase) -> ProcessingResult:
        """Execute processing actions after successful validation."""
        ...
```

**Error Handling**:
- Duplicate intent name → raise `RegistrationError("Duplicate intent: {intent_name}")`, log conflict
- Processor missing `validate` or `process` → raise `RegistrationError("Processor must implement validate and process")`

---

## DocumentValidator

**Purpose**: Verify that at least one valid Verification_Document is attached to a case before allowing data updates.

**Technology**: Python

**Responsibilities**:
- Check that at least one `VerificationDocument` is attached to the case
- Validate document status is "OK" or "valid" (case-insensitive)
- Accept the case if at least one document passes (multiple documents scenario)
- Reject and log cases with no documents or all-invalid documents

**Exposes**:
- `validate(case: SFCase) -> ValidationResult` — returns `ValidationResult(ok=True/False, reason=str, doc_id=str|None)`

**Consumes**:
- `SFCase.verification_documents: list[VerificationDocument]`

**Internal Structure**:
```
document_validator/
  ├── validator.py        # DocumentValidator class
  └── models.py           # ValidationResult dataclass
```

**Key Decisions**:
1. Case-insensitive comparison against `{"ok", "valid"}` — matches Requirement 4, AC3
2. "At least one valid" semantics for multiple documents — Requirement 4, AC5
3. Logs document identifier and status on rejection — Requirement 4, AC4

**Error Handling**:
- No documents attached → log case ID + "no verification document found", return `ValidationResult(ok=False, reason=NO_DOCUMENT)`
- All documents invalid → log case ID + each doc identifier + status, return `ValidationResult(ok=False, reason=INVALID_DOCUMENT, doc_id=first_invalid_doc_id)`

---

## CustomerDataStore

**Purpose**: Read and update customer records in local JSON storage, keyed by CID.

**Technology**: Python, `json` stdlib, `filelock` library for atomic writes

**Responsibilities**:
- Load customer records from `customer_data.json`
- Look up a record by CID
- Update only the specific field indicated by the intent (first name, title, or last name)
- Preserve all other fields unchanged
- Write updated record back atomically
- Log success (CID + field modified) and failure (CID + error)

**Exposes**:
- `update(cid: str, field: str, value: str) -> UpdateResult` — updates a single field for a customer; returns `UpdateResult(ok=True/False, reason=str)`

**Consumes**:
- `customer_data.json` — local file path from config `CUSTOMER_DATA_PATH`

**Internal Structure**:
```
customer_data_store/
  ├── store.py            # CustomerDataStore class
  └── models.py           # CustomerRecord, UpdateResult dataclasses
```

**Key Decisions**:
1. `filelock` for atomic read-modify-write — prevents corruption under concurrent pipeline runs
2. Only the field specified by the intent is updated — all other fields preserved (Requirement 5, AC2)
3. CID not found → log error, return `UpdateResult(ok=False, reason=CID_NOT_FOUND)` — does not create new records

**Error Handling**:
- CID not found → log CID + "not found in store", return `UpdateResult(ok=False, reason=CID_NOT_FOUND)`
- File I/O error → log CID + attempted operation + exception, return `UpdateResult(ok=False, reason=STORAGE_ERROR)`
- JSON parse error → log file path + exception, raise `StorageInitError` (pipeline cannot continue)

---

## PersonalInfoChangeProcessor

**Purpose**: Concrete intent processor for Customer Information Update (name/title change) intents. Composes DocumentValidator and CustomerDataStore.

**Technology**: Python

**Responsibilities**:
- Implement `IntentProcessor.validate()` — delegates to `DocumentValidator`
- Implement `IntentProcessor.process()` — determines which field to update from intent name, calls `CustomerDataStore.update()`
- Map intent name to field name (e.g., "เปลี่ยนแปลงชื่อ" → `first_name`, "เปลี่ยนแปลงนามสกุล" → `last_name`, "เปลี่ยนแปลงคำนำหน้า" → `title`)

**Exposes**:
- `validate(case: SFCase) -> ValidationResult`
- `process(case: SFCase) -> ProcessingResult`

**Consumes**:
- `DocumentValidator`
- `CustomerDataStore`

**Internal Structure**:
```
intents/
  └── personal_info_change/
      ├── processor.py    # PersonalInfoChangeProcessor class
      └── field_map.py    # Intent name → field name mapping
```

**Key Decisions**:
1. Field mapping is a dict constant — easy to extend for new sub-intents without code changes
2. Processor is registered at application startup with all known intent name strings

---

## Component Interactions

```
┌──────────────────┐
│  Pipeline Runner │
│  (main.py)       │
└────────┬─────────┘
         │ 1. extract()
         ▼
┌──────────────────┐
│ SFCaseExtractor  │──── Salesforce REST API
└────────┬─────────┘
         │ list[SFCase]
         ▼
┌──────────────────┐     ┌──────────────────┐
│  IntentAnalyzer  │────>│  IntentRegistry  │
└────────┬─────────┘     └──────────────────┘
         │ processor.validate(case)
         ▼
┌──────────────────────────────┐
│  PersonalInfoChangeProcessor │
│  ┌────────────────────────┐  │
│  │   DocumentValidator    │  │
│  └────────────┬───────────┘  │
│               │ ok           │
│  ┌────────────▼───────────┐  │
│  │   CustomerDataStore    │──┼── customer_data.json
│  └────────────────────────┘  │
└──────────────────────────────┘
         │ ProcessingResult
         ▼
┌──────────────────┐
│  Logger / Output │
└──────────────────┘
```

**Data Flow**:
1. Pipeline Runner triggers `SFCaseExtractor.extract()` → returns `list[SFCase]`
2. For each case: `IntentAnalyzer.analyze(case)` → looks up processor in `IntentRegistry`
3. Processor calls `DocumentValidator.validate(case)` → returns `ValidationResult`
4. If valid: processor calls `CustomerDataStore.update(cid, field, value)` → returns `UpdateResult`
5. `ProcessingResult` logged for every case (success, skipped, or failed)
