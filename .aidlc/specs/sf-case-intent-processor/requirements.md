# Requirements Document

## Introduction

The SF Case Intent Processor is a browser-based call center UI system that enables call center agents to process Customer Information Update requests from Salesforce. The system presents a structured 4-step workflow: the agent selects the change type (intent), enters the new value, uploads and verifies a supporting document via OCR, and confirms submission. Requests are routed to the appropriate approval level based on the intent's risk classification. All changes are tracked in a persistent audit log and surfaced in a real-time executive dashboard.

## Glossary

- **SF_Case_Extractor**: The component responsible for querying and retrieving case records from Salesforce
- **Intent_Analyzer**: The component responsible for identifying the intent name from a case and routing it to the appropriate processing logic
- **Document_Validator**: The component responsible for verifying that required documents are attached to a case and checking their validity via OCR and image analysis
- **Customer_Data_Store**: The local storage system (browser localStorage) where customer data is maintained, keyed by CID
- **CID**: Customer ID — the unique identifier used as the key for customer records in the Customer_Data_Store
- **Intent**: A categorized label describing the purpose or request type of a Salesforce case (e.g., "ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล")
- **Sub-Intent**: A specific change type within the Customer Information Update category (e.g., first name change, national ID change)
- **Verification_Document**: A document uploaded by the agent as proof for validating a customer's request (e.g., Thai National ID card, name change certificate, birth certificate)
- **Approval_Queue**: The list of pending requests that require manual review by Operations Team or Compliance Team before the customer record is updated
- **Audit_Log**: A persistent record of all before/after field changes, statuses, and agent actions
- **OCR**: Optical Character Recognition — automated text extraction from uploaded document images using Tesseract.js
- **Case**: A Salesforce record representing a customer service request

---

## Requirements

### Requirement 1: Extract Non-Closed Customer Information Update Cases from Salesforce

**User Story:** As a system operator, I want to extract all cases from Salesforce where the status is not "Closed" and the intent belongs to the Customer Information Update category, so that only relevant active cases are processed.

#### Acceptance Criteria

1. WHEN the SF_Case_Extractor is triggered, THE SF_Case_Extractor SHALL query Salesforce for all cases where the status field is not equal to "Closed" AND the intent name field matches the Customer Information Update category (e.g., "ขอใช้บริการ:CC - ข้อมูลส่วนตัว"), and return the results within 30 seconds
2. WHEN cases are retrieved from Salesforce, THE SF_Case_Extractor SHALL include at minimum the case ID, CID, intent name, and status fields for each case in the extracted data
3. IF the Salesforce query fails, returns an error, or does not respond within 30 seconds, THEN THE SF_Case_Extractor SHALL retry the query up to 3 times before logging the error details and reporting the failure without processing any cases
4. WHEN no matching cases exist in Salesforce, THE SF_Case_Extractor SHALL return an empty result set and log that zero cases were found
5. THE SF_Case_Extractor SHALL NOT retrieve cases whose intent does not belong to the Customer Information Update category, even if those cases are non-closed

---

### Requirement 2: Call Center Agent Case Processing UI

**User Story:** As a call center agent, I want a structured step-by-step UI to process Customer Information Update cases, so that I can submit changes accurately and consistently.

#### Acceptance Criteria

1. WHEN the agent opens the system, THE UI SHALL display a customer selector allowing the agent to choose the customer (CID) being processed
2. THE UI SHALL present a 4-step workflow: (1) Select Intent, (2) Enter New Value, (3) Upload & Verify Document, (4) Confirm & Submit
3. WHEN the agent selects an intent, THE UI SHALL display the intent's approval routing level (Auto-Approve, Operations Team, or Compliance Team) with a visual indicator and explanation
4. WHEN the agent enters a new value, THE UI SHALL display the customer's current value for each field being changed, so the agent can confirm the before/after difference
5. THE UI SHALL prevent progression to the next step if required fields are empty, highlighting the missing fields in red
6. WHEN the agent reaches the Confirm step, THE UI SHALL display a summary showing the case ID, CID, intent, and a before → after comparison for each field being changed
7. THE UI SHALL display a processing log showing all actions taken during the current session

---

### Requirement 3: Intent Classification and Approval Routing

**User Story:** As a system operator, I want each intent type to be automatically routed to the correct approval level, so that high-risk changes receive appropriate oversight.

#### Acceptance Criteria

1. THE system SHALL support the following 6 Customer Information Update sub-intents, each mapped to an approval level:

   | Sub-Intent | Thai Label | Approval Level |
   |---|---|---|
   | Change First Name | เปลี่ยนแปลงชื่อ | Operations Team |
   | Change Last Name | เปลี่ยนแปลงนามสกุล | Operations Team |
   | Change Title/Prefix | เปลี่ยนแปลงคำนำหน้า | Auto-Approve |
   | Change Full Name | เปลี่ยนแปลงชื่อ-นามสกุล | Operations Team |
   | Change National ID | เปลี่ยนแปลงเลขบัตรประชาชน | Compliance Team |
   | Change Date of Birth | เปลี่ยนแปลงวันเกิด | Auto-Approve |

2. WHEN the approval level is **Auto-Approve**, THE system SHALL update the customer record immediately upon agent submission without requiring manual review
3. WHEN the approval level is **Operations Team** or **Compliance Team**, THE system SHALL place the request in the Approval Queue and SHALL NOT update the customer record until a reviewer approves
4. THE system SHALL display the approval routing reason to the agent before submission, explaining why the intent requires that level of review
5. THE submit button label SHALL reflect the routing: "Submit & Apply Now" for Auto-Approve, "Submit for [Team] Approval" for manual review intents

---

### Requirement 4: Document Upload and OCR Verification

**User Story:** As a call center agent, I want to upload a supporting document and have the system automatically verify it using OCR, so that document validation is fast and consistent.

#### Acceptance Criteria

1. WHEN the agent reaches Step 3, THE system SHALL display the required document type for the selected intent:

   | Sub-Intent | Required Document |
   |---|---|
   | Change First Name | Thai National ID Card (บัตรประชาชน) |
   | Change Last Name | Thai National ID Card (บัตรประชาชน) |
   | Change Title | Thai National ID Card (บัตรประชาชน) |
   | Change Full Name | Name Change Certificate (ใบเปลี่ยนชื่อ-นามสกุล) |
   | Change National ID | New Thai National ID Card |
   | Change Date of Birth | Birth Certificate (สูติบัตร) |

2. THE system SHALL accept image files (JPG, PNG, WEBP) up to 10MB via drag-and-drop or file browser
3. WHEN a file is selected, THE system SHALL automatically start OCR verification without requiring the agent to click a separate button
4. THE OCR verification SHALL run in two phases:
   - **Phase 1 — Image Quality Analysis** (instant, no network): checks resolution (min 300×300px), aspect ratio, brightness, color variance, edge density, and Thai ID card color profile
   - **Phase 2 — Text Extraction** (requires internet on first run): uses Tesseract.js with Thai + English language packs to extract and validate document content
5. THE combined verification score SHALL be calculated as: Image Quality (40% weight) + OCR Content (60% weight)
6. IF the combined score is ≥ 80%, THE system SHALL automatically advance to the Confirm step after a 3-second countdown, which the agent can cancel
7. IF the combined score is < 80% but ≥ 60%, THE system SHALL show verification issues and allow the agent to proceed with a supervisor override
8. THE system SHALL display extracted fields (e.g., ID number, name, date) from the document so the agent can visually confirm accuracy
9. THE system SHALL validate the Thai National ID card 13-digit checksum when the document type is an ID card
10. IF OCR is unavailable (no internet connection or CDN failure), THE system SHALL display a clear message and provide a "Skip Verification" option that flags the request for manual document review
11. THE system SHALL pre-load the Tesseract.js worker in the background when the agent enters Step 3, so OCR is ready before the file is selected

---

### Requirement 5: Approval Queue Management

**User Story:** As an Operations Team or Compliance Team reviewer, I want to see all pending approval requests and be able to approve or reject them, so that customer records are updated only after proper verification.

#### Acceptance Criteria

1. THE system SHALL maintain a persistent Approval Queue (stored in browser localStorage) containing all pending, approved, and rejected requests
2. THE Approval Queue SHALL display: Approval ID, submission timestamp, case ID, CID, customer name, intent, approval level, field changes (before → after), submitting agent, and current status
3. WHEN a reviewer clicks **Approve**, THE system SHALL prompt for the reviewer's name and optional remarks, then update the customer record and mark the audit entry as APPROVED
4. WHEN a reviewer clicks **Reject**, THE system SHALL prompt for the reviewer's name and rejection reason, then mark the audit entry as REJECTED without updating the customer record
5. THE system SHALL display pending and resolved requests in separate sections
6. THE customer record SHALL NOT be updated until a reviewer explicitly approves the request

---

### Requirement 6: Customer Database

**User Story:** As a call center agent, I want to view and update customer records in a local database, so that I can process cases without requiring a live backend connection.

#### Acceptance Criteria

1. THE system SHALL maintain a customer database (browser localStorage) with the following fields per record: CID, title, first name, last name, national ID, date of birth, phone, email
2. THE system SHALL seed the database with 8 sample customer records on first load
3. WHEN a customer record is updated (auto-approved or manually approved), THE system SHALL update only the specific field indicated by the intent and preserve all other fields unchanged
4. THE system SHALL provide a "Reset to Seed Data" function that restores all customer records to their original values and clears the audit log and approval queue
5. THE Customer Database tab SHALL display all records in a table, highlighting the currently selected customer

---

### Requirement 7: Audit Log

**User Story:** As a system operator, I want a complete audit trail of all field changes, so that every update can be traced back to the agent, case, and document that authorized it.

#### Acceptance Criteria

1. THE system SHALL write an audit entry for every case submission, capturing: timestamp, case ID, CID, customer name, intent, approval level, field changed, before value, after value, agent name, and status
2. THE audit entry status SHALL reflect the current state: COMPLETED (auto-approved and applied), PENDING_APPROVAL (awaiting review), APPROVED (manually approved and applied), or REJECTED
3. WHEN a reviewer approves or rejects a request, THE system SHALL update the corresponding audit entries to reflect the new status
4. THE system SHALL display the audit log in reverse chronological order (newest first) with color-coded before (red) and after (green) values
5. THE system SHALL provide a CSV export of the audit log with UTF-8 BOM encoding for correct Thai character display in Microsoft Excel
6. THE CSV export SHALL include all fields: timestamp, case ID, CID, customer name, intent, approval level, field changed, before value, after value, agent name, status

---

### Requirement 8: Executive Dashboard

**User Story:** As a CEO or executive, I want a real-time dashboard showing case processing metrics, so that I can monitor operational performance at a glance.

#### Acceptance Criteria

1. THE dashboard SHALL display 5 KPI cards: Total Cases Today, Completed, Pending Approval, Rejected, and Approval Rate
2. EACH KPI card SHALL display: the metric value, a description of what it measures, and the formula used to calculate it
3. THE Approval Rate card SHALL display a color-coded progress bar with a target line at 80%, and a numeric breakdown (X approved · Y rejected · Z resolved)
4. THE dashboard SHALL display the following charts:
   - Bar chart: Cases by Intent Category (today)
   - Donut chart: Approval Breakdown (Completed / Pending / Approved / Rejected)
   - Donut chart: Routing Level distribution (Auto / Ops / Compliance)
   - Line chart: Daily Case Volume for the last 7 days (Completed vs Pending)
5. THE dashboard SHALL display a Recent Activity feed showing the last 20 audit entries with before/after values and timestamps
6. THE dashboard SHALL display an Intent Performance Summary table with per-intent counts, approval rates, and 7-day sparkline trends
7. THE dashboard SHALL auto-refresh every 30 seconds and display a countdown to the next refresh
8. WHEN data changes in another browser tab (agent processes a case), THE dashboard SHALL update immediately via localStorage storage events without waiting for the 30-second cycle
9. THE dashboard SHALL use a dark theme suitable for executive presentation

---

### Requirement 9: Extensible Sub-Intent Processing

**User Story:** As a developer, I want the system to support adding new Customer Information Update sub-intents without modifying existing code, so that the system can handle additional field change types in the future.

#### Acceptance Criteria

1. THE Intent registry SHALL allow new sub-intent processors to be added by defining the intent key, Thai label, English label, Salesforce intent code, fields to update, approval level, and approval reason
2. WHEN a new sub-intent is registered, THE system SHALL automatically include it in the intent selection grid, approval routing, document requirement mapping, OCR verification, audit log, and dashboard charts
3. THE system SHALL reject duplicate intent registrations and log the conflict
4. EACH registered sub-intent processor SHALL define at least one field to update and one approval level

---

## Non-Functional Requirements

### Performance
- Salesforce query SHALL complete within 30 seconds; retry up to 3 times on failure
- OCR image quality analysis (Phase 1) SHALL complete in under 1 second (canvas-based, no network)
- OCR text extraction (Phase 2) SHALL begin immediately after file selection; first-run download of language packs (~30MB) is expected and communicated to the agent

### Reliability
- Each case SHALL be processed in an isolated try/catch block; one case failure SHALL NOT halt processing of other cases
- Customer record updates SHALL be atomic (file lock / localStorage write) to prevent partial updates

### Security
- Salesforce credentials SHALL be stored in environment variables and never logged or displayed
- Customer field values (e.g., new name) SHALL NOT appear in log output — only field names and CIDs are logged
- Document images are processed entirely in the browser and are never transmitted to any external server

### Compatibility
- The system SHALL run in any modern browser (Chrome, Edge, Firefox, Safari) without installation
- No backend server, Node.js, or build step is required — all files are static HTML/CSS/JS
