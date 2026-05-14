# Requirements Document

## Introduction

The SF Case Intent Processor is a full-stack system for automating Customer Information Update requests from Salesforce. It consists of:

1. **Python Backend Pipeline** (`sf-case-intent-processor/`) — Extracts cases from a real Salesforce sandbox (cardxscb--uat), identifies intent, validates documents, updates a local customer data store, syncs changes to the Mobius API (kong-uat2-pci-clb.int-np.cardx.co.th), and closes the SF case.

2. **Call Center UI** (`Case_Update_Name/`) — A browser-based HTML/CSS/JS application where agents process cases through a 4-step workflow (select intent → enter value → verify document → confirm). Includes approval routing, audit log, and an executive dashboard.

3. **API Server** (`api_server.py`) — A lightweight localhost:5000 HTTP server bridging the UI to live Salesforce data.

## Glossary

- **SF_Case_Extractor**: Queries Salesforce sandbox for non-closed Customer Information Update cases using SOQL with `Type__c LIKE 'CC - ข้อมูลส่วนตัว%'`
- **Intent_Analyzer**: Routes cases to the correct processor based on `Type__c` field value
- **Document_Validator**: Validates verification documents attached to cases; skips validation for intents that don't require documents (phone, email, address)
- **Customer_Data_Store**: Local JSON file (`data/customer_data.json`) keyed by citizen ID (CID), with filelock for atomic writes
- **Mobius_Client**: HTTP client for the Mobius Gateway API — searches customer by CID, updates name/title/address/phone/email
- **SF_Case_Updater**: Closes Salesforce cases after successful processing (Status=Closed, Sub_Status__c=Done)
- **CID**: Citizen ID (เลขบัตรประชาชน) — 13-digit Thai national ID used as customer lookup key
- **CIF**: Customer ID in Mobius system — retrieved via `GET /customer/profile/List`
- **Intent**: A `Type__c` value from Salesforce identifying the change type (e.g., "CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงคำนำหน้า")
- **Approval_Queue**: Browser localStorage queue for requests requiring Operations Team or Compliance Team review
- **Audit_Log**: Persistent record of all before/after field changes in localStorage
- **OCR**: Tesseract.js-based document verification in the browser (Thai + English)

---

## Requirements

### Requirement 1: Extract Non-Closed Customer Information Update Cases from Salesforce

**User Story:** As a system operator, I want to extract all cases from the Salesforce sandbox where the status is not "Closed" and the Type__c belongs to the Customer Information Update category, so that only relevant active cases are processed.

#### Acceptance Criteria

1. WHEN the SF_Case_Extractor is triggered, THE system SHALL query Salesforce using SOQL with `Type__c LIKE 'CC - ข้อมูลส่วนตัว%'` AND `Status != 'Closed'`, and return results within 30 seconds
2. WHEN cases are retrieved, THE system SHALL extract the following fields per case: Id, CaseNumber, Subject, Type__c, Status, Sub_Status__c, Category__c, Customer_Name__c, Process_Add_Info_1__c (new first name / address / phone / email), Process_Add_Info_2__c (new last name), Process_Add_Info_3__c (new title), Process_Add_Info_4__c (old name), Process_Add_Info_9__c (citizen ID), ContactId, AccountId, CreatedDate
3. IF the Salesforce query fails or times out, THEN THE system SHALL retry up to 3 times with a 2-second delay before raising an ExtractionError
4. IF a SalesforceExpiredSession occurs, THE system SHALL reconnect and retry without counting it as a retry attempt
5. IF SalesforceAuthenticationFailed occurs, THE system SHALL raise ExtractionError immediately without retrying
6. WHEN no matching cases exist, THE system SHALL return an empty list and log "0 cases found"
7. THE system SHALL also fetch Attachments and ContentDocumentLinks for each case to populate verification documents

---

### Requirement 2: Intent Classification and Routing (7 Sub-Intents)

**User Story:** As a system operator, I want each case to be automatically classified and routed to the correct processing logic based on its Type__c value, so that changes are handled by the appropriate approval level.

#### Acceptance Criteria

1. THE system SHALL support the following 7 Customer Information Update sub-intents:

   | Type__c Value | Thai Label | English Label | Approval Level | Mobius Action |
   |---|---|---|---|---|
   | CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงคำนำหน้า | เปลี่ยนแปลงคำนำหน้า | Change Title/Prefix | AUTO | PUT titleCode |
   | CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล | เปลี่ยนแปลงชื่อ-นามสกุล | Change Full Name | OPS | PUT thaiFirstName + thaiLastName |
   | CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ | เปลี่ยนแปลงชื่อ | Change First Name | OPS | PUT thaiFirstName |
   | CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงนามสกุล | เปลี่ยนแปลงนามสกุล | Change Last Name | OPS | PUT thaiLastName |
   | CC - ข้อมูลส่วนตัว - ที่อยู่ | เปลี่ยนแปลงที่อยู่ | Change Address | AUTO | POST address |
   | CC - ข้อมูลส่วนตัว - หมายเลขโทรศัพท์ในการติดต่อ | เปลี่ยนแปลงเบอร์โทร | Change Phone | AUTO | POST Contacts PM |
   | CC - ข้อมูลส่วนตัว - อีเมล | เปลี่ยนแปลงอีเมล | Change Email | AUTO | POST Contacts PE |

2. WHEN the approval level is **AUTO**, THE system SHALL process the case immediately (update local store → sync Mobius → close SF case)
3. WHEN the approval level is **OPS**, THE system SHALL require Operations Team approval before Mobius sync (in UI flow); in pipeline mode, it processes and syncs directly
4. THE system SHALL use exact string matching on `Type__c` to route to the correct processor
5. IF an unrecognized intent is encountered, THE system SHALL return ProcessingResult with status=SKIPPED and reason=UNRECOGNIZED_INTENT

---

### Requirement 3: Mobius API Integration — Customer Profile Update

**User Story:** As a system operator, I want processed cases to be synced to the Mobius core banking system, so that customer profile changes are reflected in the bank's master data.

#### Acceptance Criteria

1. THE system SHALL connect to Mobius Gateway at `https://kong-uat2-pci-clb.int-np.cardx.co.th/sde-biz-cardx-mobius-gateway-ws/v1`
2. FOR each processed case, THE system SHALL first search the customer by citizen ID using `GET /customer/profile/List?searchBy=ID_NUMBER&idNumber={cid}&idType=P1` to obtain the customerId (CIF)
3. FOR title changes, THE system SHALL call `PUT /party/cust-profile` with `{"customerId": "{cif}", "titleCode": "{code}"}` where titleCode is mapped from Thai (นาย→MR., นาง→MRS., นางสาว→MISS)
4. FOR name changes, THE system SHALL call `PUT /party/cust-profile` with `{"customerId": "{cif}", "thaiFirstName": "...", "thaiLastName": "..."}`
5. FOR address changes, THE system SHALL call `POST /party/cust-profile/address` with the full address payload including addressNumber, moo, soi, thanon, subDistrict, district, province, zipCode, country, addressType, addressFormat
6. FOR phone changes, THE system SHALL call `POST /party/cust-profile/{cif}/Contacts` with `{"contactTypeCode": "PM", "contactInformation": "{phone}", "contactCategory": "PRI"}`
7. FOR email changes, THE system SHALL call `POST /party/cust-profile/{cif}/Contacts` with `{"contactTypeCode": "PE", "contactInformation": "{email}", "contactCategory": "PRI"}`
8. THE system SHALL include required headers: MBS-Authorization, Authorization, channelCode=CCRS, requestUID (UUID), correlationID (UUID)
9. IF the Mobius API call fails, THE system SHALL retry up to 3 times on timeout or HTTP 5xx; no retry on HTTP 4xx
10. Mobius sync is best-effort: IF the Mobius call fails after retries, THE local update and SF case closure SHALL still proceed; `mobius_synced=False` is recorded in the result

---

### Requirement 4: Salesforce Case Closure After Processing

**User Story:** As a system operator, I want processed cases to be automatically closed in Salesforce, so that the case queue stays clean and agents can see which cases have been handled.

#### Acceptance Criteria

1. WHEN a case is successfully processed (status=COMPLETED), THE system SHALL update the Salesforce case with `Status=Closed` and `Sub_Status__c=Done`
2. IF the SF case closure fails, THE system SHALL log a warning but NOT revert the local update or Mobius sync
3. THE system SHALL use the same Salesforce connection established during extraction to perform the update

---

### Requirement 5: Document Validation

**User Story:** As a system operator, I want the system to validate that required verification documents are attached to cases before processing, so that unauthorized changes are prevented.

#### Acceptance Criteria

1. FOR intents requiring documents (title change, name changes), THE system SHALL check that at least one Attachment or ContentDocument is linked to the case
2. FOR intents that don't require documents (phone, email, address — marked "ไม่ต้องใช้เอกสาร"), THE system SHALL skip document validation and return ValidationResult(ok=True)
3. IF no documents are attached to a case requiring them, THE system SHALL return ValidationResult(ok=False, reason="NO_DOCUMENT")
4. THE required documents per intent are:
   - Title/Name changes: Thai National ID Card (บัตรประชาชน)
   - Address: สำเนาทะเบียนบ้าน / หลักฐานที่อยู่ใหม่
   - Phone/Email: ไม่ต้องใช้เอกสาร (ยืนยันตัวตนผ่าน OTP)

---

### Requirement 6: Call Center Agent UI — 4-Step Workflow

**User Story:** As a call center agent, I want a structured step-by-step UI to process Customer Information Update cases, so that I can submit changes accurately and consistently.

#### Acceptance Criteria

1. THE UI SHALL present 5 intent cards for selection: Title, Full Name, Address, Phone, Email (matching the 5 primary Mobius-synced intents)
2. THE UI SHALL display a 4-step workflow: (1) Select Intent → (2) Enter New Value → (3) Upload & Verify Document → (4) Confirm & Submit
3. WHEN an intent is selected, THE UI SHALL show the approval routing level (Auto-Approve ✅, Operations Team 📋, or Compliance Team 🔒)
4. THE UI SHALL provide a "Refresh from Salesforce" button that calls `localhost:5000/api/cases` to fetch live case data
5. THE UI SHALL include tabs: Case Processing, Approval Queue, SF Cases (live), Customer Database, Audit Log
6. THE UI SHALL support OCR document verification using Tesseract.js with Thai + English language packs
7. THE UI SHALL maintain an approval queue in localStorage for OPS/COMPLIANCE-level requests
8. THE UI SHALL write audit entries for every submission with before/after values, timestamps, and agent info

---

### Requirement 7: Executive Dashboard

**User Story:** As a CEO or executive, I want a real-time dashboard showing case processing metrics, so that I can monitor operational performance at a glance.

#### Acceptance Criteria

1. THE dashboard SHALL display 5 KPI cards: Total Cases Today, Completed, Pending Approval, Rejected, Approval Rate
2. THE dashboard SHALL display charts: Cases by Intent (bar), Approval Breakdown (donut), Routing Level (donut), Daily Volume 7-day trend (line)
3. THE dashboard SHALL display an Intent Performance Summary table with per-intent counts and approval rates
4. THE dashboard SHALL display a Recent Activity feed showing the last 20 audit entries
5. THE dashboard SHALL auto-refresh every 30 seconds with a visible countdown
6. THE dashboard SHALL use a dark theme suitable for executive presentation
7. THE dashboard SHALL update immediately via localStorage `storage` events when data changes in another tab

---

### Requirement 8: API Server for UI-to-Salesforce Bridge

**User Story:** As a call center agent, I want the UI to fetch live case data from Salesforce without requiring direct API credentials in the browser, so that I can see real-time case status.

#### Acceptance Criteria

1. THE API server SHALL run on `localhost:5000` and expose `GET /api/cases` (returns non-closed CIU cases as JSON) and `GET /api/health`
2. THE API server SHALL include CORS headers (`Access-Control-Allow-Origin: *`) to allow browser requests
3. THE API server SHALL return case data in a UI-friendly JSON format with camelCase field names
4. THE API server SHALL be startable via `python api_server.py` or `start_server.bat`

---

### Requirement 9: Extensible Intent Processing

**User Story:** As a developer, I want to add new Customer Information Update sub-intents by editing a single configuration file, so that the system can handle additional field change types without modifying core logic.

#### Acceptance Criteria

1. THE `INTENT_FIELD_MAP` in `field_map.py` SHALL be the single source of truth for all registered intents
2. WHEN a new entry is added to `INTENT_FIELD_MAP`, THE system SHALL automatically include it in: SOQL queries (via `SUPPORTED_INTENTS`), intent routing, document validation rules, Mobius sync logic, and pipeline processing
3. EACH intent entry SHALL define: label_th, label_en, source_fields, target_fields, approval_level, required_doc
4. THE system SHALL reject duplicate intent registrations at startup via IntentRegistry

---

## Non-Functional Requirements

### Performance
- Salesforce SOQL query SHALL complete within 30 seconds; retry up to 3 times with 2s delay
- Mobius API calls SHALL timeout at 30 seconds; retry up to 3 times on 5xx/timeout
- OCR image quality analysis (Phase 1) SHALL complete in under 1 second (canvas-based, no network)
- Dashboard auto-refresh every 30 seconds; immediate update via localStorage events

### Reliability
- Each case SHALL be processed in an isolated try/except block; one case failure SHALL NOT halt processing of other cases
- Customer record updates SHALL be atomic (filelock for JSON store; single localStorage write for UI)
- Mobius sync is best-effort — local update succeeds even if Mobius fails

### Security
- Salesforce credentials stored in `.env` file (never committed, in `.gitignore`)
- Mobius API credentials hardcoded in client for UAT only (MBS-Authorization + Authorization headers)
- Customer field values (e.g., new name) SHALL NOT appear in log output — only field names and CIDs
- Document images processed entirely in browser — never transmitted externally

### Compatibility
- Backend: Python 3.11+ on Windows/Linux/macOS
- UI: Any modern browser (Chrome, Edge, Firefox, Safari) — no build step required
- API Server: localhost:5000 (no external deployment needed)

### Testing
- 84 unit + integration tests passing via pytest
- Coverage target: ≥ 80% overall, 100% on DocumentValidator and CustomerDataStore
- Test files: 8 unit test files + 1 integration test file
