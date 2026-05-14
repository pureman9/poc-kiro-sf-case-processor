# Implementation Tasks — SF Case Intent Processor

## Summary
- **Total Tasks**: 40 tasks across 9 phases in 4 execution waves
- **Strategy**: Component-First (build each module independently, integrate via pipeline runner)
- **Testing**: Test-after (unit tests per component, integration test for full pipeline)
- **Derived From**: 9 requirements, 5 components + Mobius client, 4 entities, 2 external integrations (Salesforce + Mobius)

## Overview

Tasks organized by component, following the modular monolith architecture. Each phase builds one self-contained module. The pipeline runner (Phase 7) integrates everything.

**Checkbox Legend**:
- `[ ]` — Not started
- `[x]` — Completed
- `[!]` — Blocked / Failed

**Derived From**:
- Requirements: R1–R9 from `requirements.md`
- Design: 5 components, 4 entities, 1 Salesforce integration from `design/` folder

**Strategy**: Component-First
**Rationale**: Each component has clear interfaces and no circular dependencies. Building them independently allows parallel development and isolated testing before integration.

---

- [ ] 1. Project Setup & Shared Foundation
  - [ ] 1.1 Initialize project structure
    - **Deps**: None | **Ref**: `design/implementation.md` — Directory Structure
    - Create directory layout: `sf_case_extractor/`, `intent_analyzer/`, `document_validator/`, `customer_data_store/`, `intents/personal_info_change/`, `shared/`, `tests/unit/`, `tests/integration/`, `data/`
    - Add `__init__.py` to each package directory
    - Create `requirements.txt` with pinned versions: `simple-salesforce==1.12.5`, `python-dotenv==1.0.1`, `filelock==3.13.1`, `pytest==8.2.0`, `pytest-mock==3.14.0`
    - Create `.env.example` with all required variables: `SF_USERNAME`, `SF_PASSWORD`, `SF_SECURITY_TOKEN`, `SF_DOMAIN`, `CUSTOMER_DATA_PATH`, `LOG_LEVEL`
    - Create `.gitignore` — exclude `.env`, `__pycache__/`, `.venv/`, `*.pyc`, `data/customer_data.json`

  - [ ] 1.2 Implement shared models
    - **Deps**: 1.1 | **Ref**: `design/data-model.md` — ProcessingResult, ValidationResult
    - Create `shared/models.py` — `ProcessingStatus` enum (COMPLETED, SKIPPED, FAILED), `ProcessingResult` dataclass, `ValidationResult` dataclass
    - Create `shared/exceptions.py` — `ExtractionError`, `StorageInitError`, `CIDNotFoundError`, `RegistrationError`
    - Create `shared/logger.py` — `JsonFormatter` class, `setup_logger()` function with structured JSON output

  - [ ] 1.3 Implement config loader
    - **Deps**: 1.1 | **Ref**: `design/implementation.md` — Environment Variables
    - Create `config.py` — `AppConfig` dataclass, `load_config()` function using `python-dotenv`
    - Validate required env vars on load; raise `ValueError` with clear message if missing
    - Set defaults: `CUSTOMER_DATA_PATH=./data/customer_data.json`, `LOG_LEVEL=INFO`

  - [ ] 1.4 Create seed customer data file
    - **Deps**: 1.1 | **Ref**: `design/data-model.md` — CustomerRecord JSON format
    - Create `data/customer_data.json` with 8 sample Thai customer records
    - Each record: `cid`, `first_name`, `title`, `last_name`, `national_id`, `dob`, `phone`, `email`
    - Use realistic Thai names and valid 13-digit national ID numbers (with correct checksum)

---

- [ ] 2. SFCase Data Models & SOQL Builder
  - [ ] 2.1 Implement SFCase and VerificationDocument dataclasses
    - **Deps**: 1.2 | **Ref**: `design/data-model.md` — SFCase, VerificationDocument
    - Create `sf_case_extractor/models.py` — `SFCase` dataclass, `VerificationDocument` dataclass with `is_valid()` method
    - `VerificationDocument.is_valid()`: `status.strip().lower() in {"ok", "valid"}`
    - Include `__post_init__` validation: `case_id` and `cid` must be non-empty strings

  - [ ] 2.2 Implement SOQL query builder
    - **Deps**: 2.1 | **Ref**: `design/integration.md` — SOQL Query
    - Create `sf_case_extractor/soql_builder.py` — `build_ciu_query()` function
    - Query: `SELECT Id, CID__c, Intent_Name__c, Status, New_Value__c, (SELECT Id, Status__c FROM VerificationDocuments__r) FROM Case WHERE Status != 'Closed' AND Intent_Name__c LIKE 'ขอใช้บริการ:CC - ข้อมูลส่วนตัว%'`
    - Make intent prefix configurable via parameter (default: `'ขอใช้บริการ:CC - ข้อมูลส่วนตัว%'`)

  - [ ] 2.3 Write unit tests for models and SOQL builder
    - **Deps**: 2.1, 2.2 | **Ref**: `design/integration.md` — Test Scenarios
    - `tests/unit/test_extractor_models.py`: test `VerificationDocument.is_valid()` with "OK", "valid", "ok", "VALID", "PENDING", ""
    - `tests/unit/test_soql_builder.py`: test query string contains correct WHERE clause, test custom intent prefix

---

- [ ] 3. SFCaseExtractor
  - [ ] 3.1 Implement SFCaseExtractor class
    - **Deps**: 2.1, 2.2, 1.3 | **Ref**: `design/components.md` — SFCaseExtractor, `design/integration.md` — Retry Logic
    - Create `sf_case_extractor/extractor.py` — `SFCaseExtractor` class
    - `__init__(config)`: initialize `simple_salesforce.Salesforce` client from config
    - `extract() -> list[SFCase]`: execute SOQL, parse response, return list of `SFCase` objects
    - Retry loop: `MAX_RETRIES=3`, `RETRY_DELAY_SECONDS=2`, `QUERY_TIMEOUT_SECONDS=30`
    - Map Salesforce response fields to `SFCase` dataclass (Id→case_id, CID__c→cid, etc.)
    - Map related list `VerificationDocuments__r` to `list[VerificationDocument]`
    - Log: extraction start, case count on success, retry warnings, final error

  - [ ] 3.2 Implement error handling for Salesforce failures
    - **Deps**: 3.1 | **Ref**: `design/integration.md` — Error Handling table
    - Handle `SalesforceAuthenticationFailed` → raise `ExtractionError` immediately (no retry)
    - Handle `SalesforceExpiredSession` → re-authenticate once, retry query
    - Handle network timeout → retry up to 3 times, then raise `ExtractionError`
    - Handle HTTP 4xx → raise `ExtractionError` immediately
    - Handle HTTP 5xx → retry up to 3 times, then raise `ExtractionError`
    - Empty result → return `[]`, log "0 cases found matching criteria"

  - [ ] 3.3 Write unit tests for SFCaseExtractor
    - **Deps**: 3.1, 3.2 | **Ref**: `design/integration.md` — Test Scenarios
    - Create `tests/unit/test_extractor.py` with `pytest-mock`
    - Test: successful query returns correct `SFCase` list
    - Test: query timeout → retries 3 times → raises `ExtractionError`
    - Test: auth failure → immediate `ExtractionError` (no retry)
    - Test: empty result → returns `[]`
    - Test: HTTP 5xx → retries 3 times → raises `ExtractionError`
    - Test: response with verification documents → correctly mapped to `VerificationDocument` list

---

- [ ] 4. Intent Analyzer & Registry
  - [ ] 4.1 Implement IntentProcessor ABC
    - **Deps**: 1.2 | **Ref**: `design/components.md` — IntentRegistry, IntentProcessor Interface
    - Create `intent_analyzer/base_processor.py` — `IntentProcessor` ABC
    - Abstract methods: `validate(case: SFCase) -> ValidationResult`, `process(case: SFCase) -> ProcessingResult`
    - Use `abc.ABC` and `@abstractmethod` decorators — Python enforces at class definition time

  - [ ] 4.2 Implement IntentRegistry
    - **Deps**: 4.1 | **Ref**: `design/components.md` — IntentRegistry
    - Create `intent_analyzer/registry.py` — `IntentRegistry` class
    - `register(intent_name: str, processor: IntentProcessor) -> None`: validate processor implements ABC, check for duplicates, store in dict
    - `get(intent_name: str) -> IntentProcessor | None`: O(1) dict lookup
    - Raise `RegistrationError` on duplicate or invalid processor
    - Create `intent_analyzer/exceptions.py` — `MissingIntentError`, `UnrecognizedIntentError`, `RegistrationError`

  - [ ] 4.3 Implement IntentAnalyzer
    - **Deps**: 4.2, 1.2 | **Ref**: `design/components.md` — IntentAnalyzer
    - Create `intent_analyzer/analyzer.py` — `IntentAnalyzer` class
    - `__init__(registry: IntentRegistry)`: store registry reference
    - `analyze(case: SFCase) -> ProcessingResult`: extract intent_name, validate non-empty, look up processor, call validate() then process()
    - Per-case try/except: catch all exceptions, log case_id + exception, return `ProcessingResult(status=FAILED)`
    - Return `ProcessingResult(status=SKIPPED, reason=MISSING_INTENT)` for empty intent
    - Return `ProcessingResult(status=SKIPPED, reason=UNRECOGNIZED_INTENT)` for unknown intent

  - [ ] 4.4 Write unit tests for IntentAnalyzer and IntentRegistry
    - **Deps**: 4.2, 4.3 | **Ref**: `design/components.md` — Error Handling sections
    - Create `tests/unit/test_intent_registry.py`: test register success, duplicate rejection, missing method rejection, get existing, get non-existing
    - Create `tests/unit/test_intent_analyzer.py`: test empty intent → SKIPPED, unrecognized intent → SKIPPED, processor exception → FAILED, successful routing → calls validate() and process()

---

- [ ] 5. Document Validator
  - [ ] 5.1 Implement DocumentValidator
    - **Deps**: 2.1, 1.2 | **Ref**: `design/components.md` — DocumentValidator
    - Create `document_validator/validator.py` — `DocumentValidator` class
    - `validate(case: SFCase) -> ValidationResult`:
      - If `len(case.verification_documents) == 0` → return `ValidationResult(ok=False, reason="NO_DOCUMENT")`
      - If any document `is_valid()` → return `ValidationResult(ok=True)`
      - Else → log each invalid doc (case_id, doc_id, status), return `ValidationResult(ok=False, reason="INVALID_DOCUMENT", doc_id=first_invalid.doc_id)`
    - Create `document_validator/models.py` — `ValidationResult` dataclass (ok, reason, doc_id)

  - [ ] 5.2 Write unit tests for DocumentValidator
    - **Deps**: 5.1 | **Ref**: `design/components.md` — DocumentValidator Error Handling
    - Create `tests/unit/test_document_validator.py`
    - Test: no documents → `ok=False`, `reason=NO_DOCUMENT`
    - Test: one valid document ("OK") → `ok=True`
    - Test: one valid document ("valid") → `ok=True`
    - Test: one valid document ("OK", case-insensitive) → `ok=True`
    - Test: all invalid documents → `ok=False`, `reason=INVALID_DOCUMENT`
    - Test: multiple documents, one valid → `ok=True` (at-least-one semantics)
    - Test: multiple documents, all invalid → `ok=False`

---

- [ ] 6. Customer Data Store
  - [ ] 6.1 Implement CustomerDataStore
    - **Deps**: 1.2, 1.3 | **Ref**: `design/components.md` — CustomerDataStore, `design/integration.md` — Atomic Write Pattern
    - Create `customer_data_store/store.py` — `CustomerDataStore` class
    - `__init__(data_path: str)`: validate file exists and is valid JSON; raise `StorageInitError` if not
    - `update(cid: str, field: str, value: str) -> UpdateResult`:
      - Acquire `FileLock` with 10s timeout
      - Load JSON, check CID exists (raise `CIDNotFoundError` if not)
      - Update only the specified field, preserve all others
      - Write back with `ensure_ascii=False, indent=2`
      - Log: CID + field_updated on success; CID + error on failure
    - Create `customer_data_store/models.py` — `CustomerRecord`, `UpdateResult` dataclasses

  - [ ] 6.2 Write unit tests for CustomerDataStore
    - **Deps**: 6.1 | **Ref**: `design/integration.md` — Test Scenarios
    - Create `tests/unit/test_customer_data_store.py` using `tmp_path` pytest fixture
    - Test: update `first_name` → only `first_name` changes, all other fields preserved
    - Test: update `last_name` → only `last_name` changes
    - Test: update `title` → only `title` changes
    - Test: CID not found → `UpdateResult(ok=False, reason=CID_NOT_FOUND)`
    - Test: file not found → raises `StorageInitError`
    - Test: invalid JSON → raises `StorageInitError`
    - Test: file I/O error during write → `UpdateResult(ok=False, reason=STORAGE_ERROR)`

---

- [ ] 7. PersonalInfoChangeProcessor & Intent Registration
  - [ ] 7.1 Implement field mapping
    - **Deps**: 4.1 | **Ref**: `design/components.md` — PersonalInfoChangeProcessor
    - Create `intents/personal_info_change/field_map.py` — `INTENT_FIELD_MAP` dict
    - Map all known intent name strings to field names:
      - `"ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ"` → `"first_name"`
      - `"ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงนามสกุล"` → `"last_name"`
      - `"ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงคำนำหน้า"` → `"title"`
      - `"ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล"` → `"first_name"` (primary; handle both fields)
    - Define `SUPPORTED_INTENTS: list[str]` — all keys from the map

  - [ ] 7.2 Implement PersonalInfoChangeProcessor
    - **Deps**: 7.1, 5.1, 6.1, 4.1 | **Ref**: `design/components.md` — PersonalInfoChangeProcessor
    - Create `intents/personal_info_change/processor.py` — `PersonalInfoChangeProcessor(IntentProcessor)`
    - `__init__(doc_validator: DocumentValidator, data_store: CustomerDataStore)`
    - `validate(case: SFCase) -> ValidationResult`: delegate to `doc_validator.validate(case)`
    - `process(case: SFCase) -> ProcessingResult`:
      - Look up field from `INTENT_FIELD_MAP[case.intent_name]`
      - Call `data_store.update(case.cid, field, case.new_value)`
      - Return `ProcessingResult(status=COMPLETED, field_updated=field, cid=case.cid)` on success
      - Return `ProcessingResult(status=FAILED, reason=result.reason)` on failure

  - [ ] 7.3 Write unit tests for PersonalInfoChangeProcessor
    - **Deps**: 7.2 | **Ref**: `design/components.md` — PersonalInfoChangeProcessor
    - Create `tests/unit/test_personal_info_processor.py` with `pytest-mock`
    - Test: validate() delegates to DocumentValidator
    - Test: process() maps intent name to correct field
    - Test: process() calls data_store.update() with correct (cid, field, value)
    - Test: process() returns COMPLETED on successful update
    - Test: process() returns FAILED when data_store returns error

---

- [ ] 8. Pipeline Runner & Integration
  - [ ] 8.1 Implement main.py pipeline runner
    - **Deps**: 3.1, 4.3, 7.2 | **Ref**: `design/implementation.md` — Pipeline Runner
    - Create `main.py` — `build_registry()` and `run()` functions
    - `build_registry()`: instantiate `DocumentValidator`, `CustomerDataStore`, `PersonalInfoChangeProcessor`, register all `SUPPORTED_INTENTS`
    - `run()`: load config, init components, call `extractor.extract()`, loop over cases calling `analyzer.analyze()`, log summary
    - Handle `ExtractionError` and `StorageInitError` at pipeline level — log and exit gracefully
    - Print final summary: `{completed} completed, {skipped} skipped, {failed} failed`

  - [ ] 8.2 Write integration test for full pipeline
    - **Deps**: 8.1 | **Ref**: `design/integration.md` — Integration Testing
    - Create `tests/integration/test_pipeline.py`
    - Use `pytest-mock` to mock `simple_salesforce.Salesforce`
    - Use `tmp_path` fixture for `customer_data.json`
    - Test: 3 cases (1 valid CIU, 1 missing intent, 1 invalid document) → correct COMPLETED/SKIPPED/SKIPPED results
    - Test: Salesforce failure → pipeline aborts with `ExtractionError`, no customer records modified
    - Test: valid case with correct document → customer record updated with correct field only
    - Test: valid case, CID not in store → FAILED result, no other records modified

  - [ ] 8.3 Verify coverage and run full test suite
    - **Deps**: 8.2 | **Ref**: `design/nfr.md` — Testing
    - Run `pytest --cov=. --cov-report=term-missing`
    - Ensure overall coverage ≥ 80%
    - Ensure `document_validator/` and `customer_data_store/` coverage = 100%
    - Fix any failing tests before marking complete

---

- [ ] 9. Mobius API Integration — Sync Customer Name Update
  - [ ] 9.1 Implement Mobius API client
    - **Deps**: 1.2, 1.3 | **Ref**: External system — Mobius API
    - Create `mobius_client/` module with `__init__.py`
    - Create `mobius_client/client.py` — `MobiusClient` class
    - `__init__(config)`: initialize HTTP client with Mobius API base URL, API key/token from config
    - `update_customer_name(cid: str, title: str, first_name: str, last_name: str) -> MobiusResult`: POST/PUT to Mobius endpoint
    - Add env vars to config: `MOBIUS_API_URL`, `MOBIUS_API_KEY`, `MOBIUS_TIMEOUT` (default 30s)
    - Add to `.env.example`: `MOBIUS_API_URL=https://api.mobius.example.com/v1`, `MOBIUS_API_KEY=[your-key]`
    - Create `mobius_client/models.py` — `MobiusResult` dataclass (ok, status_code, response_body, error)

  - [ ] 9.2 Implement retry and error handling for Mobius API
    - **Deps**: 9.1 | **Ref**: `design/nfr.md` — Retry pattern
    - Retry up to 3 times on network timeout or HTTP 5xx
    - No retry on HTTP 4xx (client error — bad request, unauthorized)
    - Log: request start, success (CID + status code), retry warning, final failure
    - Return `MobiusResult(ok=False, error=...)` on failure — do NOT raise exception (pipeline continues)

  - [ ] 9.3 Integrate Mobius call into PersonalInfoChangeProcessor
    - **Deps**: 9.1, 7.2 | **Ref**: `design/components.md` — PersonalInfoChangeProcessor
    - Modify `PersonalInfoChangeProcessor.__init__()` to accept optional `MobiusClient`
    - After successful `CustomerDataStore.update()`, call `mobius_client.update_customer_name(cid, title, first_name, last_name)`
    - If Mobius call fails: log warning but still return `ProcessingResult(status=COMPLETED)` — local update succeeded, Mobius sync is best-effort
    - Add `mobius_synced: bool` field to `ProcessingResult` to track sync status
    - Log: "Mobius sync success — CID: {cid}" or "Mobius sync failed — CID: {cid}, error: {error}"

  - [ ] 9.4 Add Mobius client to pipeline runner registration
    - **Deps**: 9.3, 8.1 | **Ref**: `design/implementation.md` — Pipeline Runner
    - Update `main.py` `build_registry()` to instantiate `MobiusClient(config)` and pass to `PersonalInfoChangeProcessor`
    - Add `MOBIUS_API_URL` and `MOBIUS_API_KEY` to `config.py` `AppConfig`
    - If `MOBIUS_API_URL` is not set → skip Mobius integration (log info: "Mobius API not configured — sync disabled")

  - [ ] 9.5 Write unit tests for Mobius client
    - **Deps**: 9.1, 9.2 | **Ref**: Test strategy
    - Create `tests/unit/test_mobius_client.py` with `pytest-mock`
    - Test: successful POST → `MobiusResult(ok=True, status_code=200)`
    - Test: timeout → retries 3 times → `MobiusResult(ok=False, error="timeout")`
    - Test: HTTP 401 → no retry → `MobiusResult(ok=False, error="unauthorized")`
    - Test: HTTP 500 → retries 3 times → `MobiusResult(ok=False, error="server error")`
    - Test: Mobius not configured (URL=None) → skip gracefully

  - [ ] 9.6 Write integration test for pipeline with Mobius sync
    - **Deps**: 9.3, 8.2 | **Ref**: Integration testing
    - Add test case to `tests/integration/test_pipeline.py`
    - Test: valid case → local update + Mobius API called with correct payload (mocked)
    - Test: valid case + Mobius failure → local update succeeds, `mobius_synced=False` in result
    - Test: Mobius not configured → pipeline runs normally without Mobius call

---

## Task Summary

| Task | Title | Dependencies | Status |
|------|-------|--------------|--------|
| 1.1 | Initialize project structure | None | [ ] |
| 1.2 | Implement shared models | 1.1 | [ ] |
| 1.3 | Implement config loader | 1.1 | [ ] |
| 1.4 | Create seed customer data file | 1.1 | [ ] |
| 2.1 | Implement SFCase and VerificationDocument dataclasses | 1.2 | [ ] |
| 2.2 | Implement SOQL query builder | 2.1 | [ ] |
| 2.3 | Write unit tests for models and SOQL builder | 2.1, 2.2 | [ ] |
| 3.1 | Implement SFCaseExtractor class | 2.1, 2.2, 1.3 | [ ] |
| 3.2 | Implement error handling for Salesforce failures | 3.1 | [ ] |
| 3.3 | Write unit tests for SFCaseExtractor | 3.1, 3.2 | [ ] |
| 4.1 | Implement IntentProcessor ABC | 1.2 | [ ] |
| 4.2 | Implement IntentRegistry | 4.1 | [ ] |
| 4.3 | Implement IntentAnalyzer | 4.2, 1.2 | [ ] |
| 4.4 | Write unit tests for IntentAnalyzer and IntentRegistry | 4.2, 4.3 | [ ] |
| 5.1 | Implement DocumentValidator | 2.1, 1.2 | [ ] |
| 5.2 | Write unit tests for DocumentValidator | 5.1 | [ ] |
| 6.1 | Implement CustomerDataStore | 1.2, 1.3 | [ ] |
| 6.2 | Write unit tests for CustomerDataStore | 6.1 | [ ] |
| 7.1 | Implement field mapping | 4.1 | [ ] |
| 7.2 | Implement PersonalInfoChangeProcessor | 7.1, 5.1, 6.1, 4.1 | [ ] |
| 7.3 | Write unit tests for PersonalInfoChangeProcessor | 7.2 | [ ] |
| 8.1 | Implement main.py pipeline runner | 3.1, 4.3, 7.2 | [ ] |
| 8.2 | Write integration test for full pipeline | 8.1 | [ ] |
| 8.3 | Verify coverage and run full test suite | 8.2 | [ ] |
| 9.1 | Implement Mobius API client | 1.2, 1.3 | [ ] |
| 9.2 | Implement retry and error handling for Mobius API | 9.1 | [ ] |
| 9.3 | Integrate Mobius call into PersonalInfoChangeProcessor | 9.1, 7.2 | [ ] |
| 9.4 | Add Mobius client to pipeline runner registration | 9.3, 8.1 | [ ] |
| 9.5 | Write unit tests for Mobius client | 9.1, 9.2 | [ ] |
| 9.6 | Write integration test for pipeline with Mobius sync | 9.3, 8.2 | [ ] |

---

## Requirements Coverage

| Requirement | Implemented By | Status |
|-------------|----------------|--------|
| R1: Extract non-closed CIU cases | 2.2, 3.1, 3.2 | [ ] |
| R2: Identify sub-intent | 4.2, 4.3 | [ ] |
| R3: Analyze by sub-intent | 4.3, 7.2 | [ ] |
| R4: Validate verification document | 5.1, 7.2 | [ ] |
| R5: Update customer data | 6.1, 7.2 | [ ] |
| R6: Extensible intent processing | 4.1, 4.2, 7.1 | [ ] |
| NFR Retry/Timeout | 3.1, 3.2 | [ ] |
| NFR Per-case isolation | 4.3, 8.1 | [ ] |
| NFR Atomic writes | 6.1 | [ ] |
| NFR Structured logging | 1.2, 3.1, 4.3, 6.1 | [ ] |

---

## Design Coverage

**Components**: 5 components → Tasks 3.1 (SFCaseExtractor), 4.2+4.3 (IntentAnalyzer+Registry), 5.1 (DocumentValidator), 6.1 (CustomerDataStore), 7.2 (PersonalInfoChangeProcessor)
**Entities**: 4 entities → Tasks 2.1 (SFCase, VerificationDocument), 6.1 (CustomerRecord), 1.2 (ProcessingResult, ValidationResult)
**Integrations**: 1 (Salesforce REST API) → Tasks 2.2, 3.1, 3.2

---

## Definition of Done

- [ ] All unit tests passing (`pytest tests/unit/`)
- [ ] Integration test passing (`pytest tests/integration/`)
- [ ] Coverage ≥ 80% overall, 100% on DocumentValidator and CustomerDataStore
- [ ] No hardcoded credentials — all config via `.env`
- [ ] Structured JSON logging for all case outcomes
- [ ] `python main.py` runs end-to-end with mocked Salesforce data

---

## Execution Waves

| Wave | Phases | Can Run In Parallel |
|------|--------|---------------------|
| 1 | Phase 1 (Project Setup) | No — foundation for all |
| 2 | Phase 2 (Data Models), Phase 4 (Intent ABC), Phase 5 (DocumentValidator), Phase 6 (CustomerDataStore), Phase 9.1–9.2 (Mobius Client) | Yes — all independent |
| 3 | Phase 3 (SFCaseExtractor), Phase 7 (PersonalInfoChangeProcessor + Mobius integration) | Yes — depend on Wave 2 only |
| 4 | Phase 8 (Pipeline Runner & Integration), Phase 9.4–9.6 (Mobius pipeline integration + tests) | No — integrates all components |

### File Ownership Per Wave

**Wave 2** (parallel):
- Phase 2: `sf_case_extractor/models.py`, `sf_case_extractor/soql_builder.py`, `tests/unit/test_extractor_models.py`, `tests/unit/test_soql_builder.py`
- Phase 4: `intent_analyzer/base_processor.py`, `intent_analyzer/registry.py`, `intent_analyzer/analyzer.py`, `intent_analyzer/exceptions.py`, `tests/unit/test_intent_registry.py`, `tests/unit/test_intent_analyzer.py`
- Phase 5: `document_validator/validator.py`, `document_validator/models.py`, `tests/unit/test_document_validator.py`
- Phase 6: `customer_data_store/store.py`, `customer_data_store/models.py`, `tests/unit/test_customer_data_store.py`
- Phase 9.1–9.2: `mobius_client/client.py`, `mobius_client/models.py`, `tests/unit/test_mobius_client.py`

**Wave 3** (parallel):
- Phase 3: `sf_case_extractor/extractor.py`, `tests/unit/test_extractor.py`
- Phase 7 + 9.3: `intents/personal_info_change/field_map.py`, `intents/personal_info_change/processor.py`, `tests/unit/test_personal_info_processor.py`

---

## Notes

**Open Questions** (from design.md — must resolve before implementation):
1. Confirm exact Salesforce custom field names: `CID__c`, `Intent_Name__c`, `New_Value__c`, `VerificationDocuments__r`, `Status__c`
2. Enumerate all Customer Information Update intent name strings beyond the examples given
3. Confirm file locking behavior under concurrent pipeline runs in production environment

**Technical Debt**:
- SOQL pagination not implemented — will fail silently if result set > 2000 records (Salesforce default limit)
- `customer_data.json` not suitable for production — replace with proper database in production phase

**Future Enhancements** (deferred from requirements):
- Salesforce case status update after processing (mark case as Closed)
- Support for additional intent categories beyond Customer Information Update
- Batch JSON writes (load once, update all, write once) for high-volume runs
