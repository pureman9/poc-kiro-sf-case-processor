# Integration Specifications

## Overview

The SF Case Intent Processor has one external integration: the Salesforce REST API (via SOQL). All other data operations are local (JSON file). There is no inter-service communication — this is a single-process pipeline.

---

## External Integrations

### Salesforce REST API

**Purpose**: Query non-closed Customer Information Update cases for processing.
**Type**: REST API (SOQL query via Salesforce REST API)
**Library**: `simple_salesforce` Python library
**Auth**: Username + Password + Security Token (stored in `.env` file, never committed)

**Connection Config** (from environment variables):
| Variable | Description | Example |
|---|---|---|
| `SF_USERNAME` | Salesforce login username | `user@example.com` |
| `SF_PASSWORD` | Salesforce login password | `[secret]` |
| `SF_SECURITY_TOKEN` | Salesforce security token | `[secret]` |
| `SF_DOMAIN` | Salesforce domain | `login` or `test` (sandbox) |

**SOQL Query**:
```sql
SELECT Id, CID__c, Intent_Name__c, Status,
       New_Value__c,
       (SELECT Id, Status__c FROM VerificationDocuments__r)
FROM Case
WHERE Status != 'Closed'
  AND Intent_Name__c LIKE 'ขอใช้บริการ:CC - ข้อมูลส่วนตัว%'
```

> ⚠️ **Open Question**: The exact Salesforce API field names (`CID__c`, `Intent_Name__c`, `New_Value__c`, `VerificationDocuments__r`, `Status__c`) are assumed based on requirements. These must be confirmed against the actual Salesforce org schema before implementation.

**Response Mapping**:
| Salesforce Field | SFCase Field | Notes |
|---|---|---|
| `Id` | `case_id` | Salesforce record ID |
| `CID__c` | `cid` | Custom field — Customer ID |
| `Intent_Name__c` | `intent_name` | Custom field — full intent string |
| `Status` | `status` | Standard field |
| `New_Value__c` | `new_value` | Custom field — new value to apply |
| `VerificationDocuments__r[].Id` | `verification_documents[].doc_id` | Related list |
| `VerificationDocuments__r[].Status__c` | `verification_documents[].status` | Related list custom field |

**Error Handling**:

| Error Type | Behavior |
|---|---|
| `SalesforceAuthenticationFailed` | Log error, raise `ExtractionError` immediately (no retry) |
| `SalesforceExpiredSession` | Re-authenticate once, retry query |
| Network timeout (>30s) | Retry up to 3 times with 2s fixed delay between attempts |
| HTTP 4xx (client error) | Log error + status code, raise `ExtractionError` immediately |
| HTTP 5xx (server error) | Retry up to 3 times, then raise `ExtractionError` |
| Empty result set | Return `[]`, log "0 cases found matching criteria" |

**Retry Logic**:
```python
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
QUERY_TIMEOUT_SECONDS = 30

for attempt in range(1, MAX_RETRIES + 1):
    try:
        result = sf.query(soql, timeout=QUERY_TIMEOUT_SECONDS)
        return parse_cases(result)
    except (SalesforceError, TimeoutError) as e:
        if attempt == MAX_RETRIES:
            logger.error(f"Extraction failed after {MAX_RETRIES} attempts: {e}")
            raise ExtractionError(str(e))
        logger.warning(f"Attempt {attempt} failed, retrying in {RETRY_DELAY_SECONDS}s: {e}")
        time.sleep(RETRY_DELAY_SECONDS)
```

---

## Local Storage Integration

### customer_data.json

**Purpose**: Persistent store for customer records, updated by the pipeline.
**Type**: Local JSON file
**Access Pattern**: Read-modify-write with file lock

**File Location**: Configured via `CUSTOMER_DATA_PATH` environment variable (default: `./data/customer_data.json`)

**Atomic Write Pattern**:
```python
from filelock import FileLock

lock = FileLock(f"{CUSTOMER_DATA_PATH}.lock")

with lock:
    with open(CUSTOMER_DATA_PATH, "r") as f:
        data = json.load(f)
    
    if cid not in data:
        raise CIDNotFoundError(cid)
    
    data[cid][field] = value  # Update only the specified field
    
    with open(CUSTOMER_DATA_PATH, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

**Error Handling**:
| Error Type | Behavior |
|---|---|
| CID not in JSON | Log CID + "not found", return `UpdateResult(ok=False, reason=CID_NOT_FOUND)` |
| File not found | Raise `StorageInitError` — pipeline cannot continue |
| JSON parse error | Raise `StorageInitError` — pipeline cannot continue |
| File I/O error during write | Log CID + operation + exception, return `UpdateResult(ok=False, reason=STORAGE_ERROR)` |
| Lock timeout | Log warning, return `UpdateResult(ok=False, reason=LOCK_TIMEOUT)` |

---

## Integration Testing

**Strategy**: Mock Salesforce API in unit and integration tests using `pytest-mock`. Use a test fixture JSON file for CustomerDataStore tests.

**Mocking**:
- `simple_salesforce.Salesforce` → mocked with `pytest-mock` in all unit tests
- `customer_data.json` → replaced with a temp file fixture in tests (`tmp_path` pytest fixture)

**Test Scenarios**:
| Scenario | Test Type |
|---|---|
| Successful Salesforce query returns cases | Unit |
| Salesforce query times out → retries 3 times → raises ExtractionError | Unit |
| Salesforce auth failure → immediate ExtractionError | Unit |
| Empty Salesforce result → returns [] | Unit |
| CustomerDataStore updates correct field only | Unit |
| CustomerDataStore CID not found → UpdateResult(ok=False) | Unit |
| Full pipeline: extract → analyze → validate → update | Integration |
