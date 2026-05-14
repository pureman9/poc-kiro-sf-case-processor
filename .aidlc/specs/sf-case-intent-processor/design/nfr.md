# Non-Functional Requirements

## Overview

NFR analysis for the SF Case Intent Processor, derived from explicit requirements (retry logic, timeout, per-case isolation) and implicit operational needs (logging, data integrity, extensibility).

---

## Reliability

### R1: Salesforce Query Retry (Requirement 1, AC3)

| Attribute | Specification |
|---|---|
| Max retries | 3 attempts |
| Retry delay | 2 seconds fixed between attempts |
| Timeout per attempt | 30 seconds |
| Failure behavior | Log error details, raise `ExtractionError`, halt pipeline (no cases processed) |
| Auth failure | No retry — fail immediately |

**Rationale**: Transient network issues are common with external APIs. 3 retries with a 2s delay gives ~36s total window before giving up, staying within reasonable batch processing expectations.

### R2: Per-Case Error Isolation (Requirement 3, AC4)

| Attribute | Specification |
|---|---|
| Scope | Each case is processed in an independent try/except block |
| Failure behavior | Log case ID + intent name + reason; continue to next case |
| Pipeline halt conditions | Only `ExtractionError` (Salesforce failure) or `StorageInitError` (JSON file unreadable) halt the entire pipeline |

**Rationale**: A single malformed case or unexpected data should not block processing of all other valid cases.

---

## Data Integrity

### R3: Atomic Customer Record Updates (Requirement 5)

| Attribute | Specification |
|---|---|
| Mechanism | `filelock` — exclusive file lock before read-modify-write |
| Lock timeout | 10 seconds (configurable via `LOCK_TIMEOUT_SECONDS`) |
| Partial write protection | Write to temp file, then atomic rename (or filelock ensures single writer) |
| Field isolation | Only the field specified by the intent is modified — all other fields preserved |

**Rationale**: Without locking, concurrent pipeline runs (e.g., triggered simultaneously) could corrupt the JSON file. Field isolation ensures no accidental data loss.

### R4: No Unauthorized Updates

| Attribute | Specification |
|---|---|
| Guard | Document validation must pass before `CustomerDataStore.update()` is called |
| Enforcement | `PersonalInfoChangeProcessor.process()` is only called after `validate()` returns `ok=True` |
| Audit | Every update attempt (success or failure) is logged with CID and field |

---

## Observability

### R5: Structured Logging

| Attribute | Specification |
|---|---|
| Format | JSON (one object per line) |
| Required fields | `timestamp`, `level`, `logger`, `message` |
| Case-level fields | `case_id` (always), `cid` (when available), `intent_name` (when available) |
| Log level | Configurable via `LOG_LEVEL` env var (default: `INFO`) |

**Log coverage** — every case must produce at least one log entry:
- ✅ Completed: INFO with `case_id`, `cid`, `field_updated`
- ✅ Skipped (missing intent): WARNING with `case_id`, `reason`
- ✅ Skipped (unrecognized intent): WARNING with `case_id`, `intent_name`
- ✅ Skipped (no document): WARNING with `case_id`
- ✅ Skipped (invalid document): WARNING with `case_id`, `doc_id`, `doc_status`
- ✅ Failed (CID not found): ERROR with `case_id`, `cid`
- ✅ Failed (storage error): ERROR with `case_id`, `cid`, `operation`, `error`

---

## Extensibility

### R6: Intent Registration (Requirement 6)

| Attribute | Specification |
|---|---|
| Interface | `IntentProcessor` ABC with `validate()` and `process()` abstract methods |
| Registration | `IntentRegistry.register(intent_name, processor)` — O(1) dict insert |
| Lookup | `IntentRegistry.get(intent_name)` — O(1) dict lookup |
| Duplicate detection | Raises `RegistrationError` at registration time |
| Missing method detection | ABC enforcement at class definition time (Python `ABCMeta`) |

**Adding a new intent** requires:
1. Create a new class in `intents/` implementing `IntentProcessor`
2. Register it in `main.py`'s `build_registry()` function
3. No changes to `IntentAnalyzer`, `IntentRegistry`, or any existing processor

---

## Performance

### R7: Pipeline Throughput

| Attribute | Specification |
|---|---|
| Expected case volume | Not specified in requirements — assumed low-to-medium (< 1000 cases per run) |
| Processing model | Sequential (one case at a time) — sufficient for current scope |
| Salesforce query | Single SOQL query for all cases — not paginated unless result set > 2000 records (Salesforce default limit) |
| JSON file I/O | One read + one write per successfully updated case — acceptable for < 1000 cases |

**Scaling note**: If case volume grows beyond ~1000 per run, consider:
- Paginating the SOQL query (`queryMore`)
- Batching JSON file writes (load once, update all, write once)

---

## Security

### R8: Credential Management

| Attribute | Specification |
|---|---|
| Storage | `.env` file — never committed to version control |
| `.gitignore` | `.env` must be listed |
| Runtime | Loaded via `python-dotenv` at startup |
| Logging | Credentials must NEVER appear in log output |

### R9: Data Handling

| Attribute | Specification |
|---|---|
| Customer data | Stored in local JSON file — access controlled by OS file permissions |
| PII in logs | Log only CID and field name — never log field values (e.g., never log the new first name) |
