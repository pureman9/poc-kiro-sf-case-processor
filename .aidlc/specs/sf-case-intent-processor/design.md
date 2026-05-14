# Design Document: SF Case Intent Processor

## Summary
- **Architecture**: Pipeline / Modular Monolith — sequential processing stages with pluggable intent processors via Strategy pattern + browser-based Call Center UI
- **Stack**: Python 3.11+ / simple_salesforce / requests / JSON file store + HTML/CSS/JS (Tesseract.js, Chart.js)
- **Components**: 8 — SFCaseExtractor, SFCaseUpdater, IntentAnalyzer, IntentRegistry, DocumentValidator, CustomerDataStore, MobiusClient, APIServer
- **Entities**: 5 — SFCase, VerificationDocument, CustomerRecord, ProcessingResult, MobiusResult
- **Integrations**: 2 — Salesforce REST API (sandbox), Mobius Gateway API (UAT)
- **Testing**: 84 unit + integration tests, pytest + pytest-mock
- **Key Decisions**: Python pipeline runner, Strategy pattern for intent registry, JSON file as local store, Mobius best-effort sync, SF case auto-closure

## Architecture

### System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SF Case Intent Processor                            │
│                                                                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │  SFCaseExtractor │───>│  IntentAnalyzer  │───>│  PersonalInfo    │      │
│  │  (SOQL query)    │    │  + IntentRegistry│    │  ChangeProcessor │      │
│  └──────────────────┘    └──────────────────┘    └────────┬─────────┘      │
│           │                                               │                 │
│           │                                    ┌──────────┼──────────┐      │
│           │                                    ▼          ▼          ▼      │
│           │                              ┌─────────┐ ┌─────────┐ ┌──────┐  │
│           │                              │Doc      │ │Customer │ │Mobius │  │
│           │                              │Validator│ │DataStore│ │Client │  │
│           │                              └─────────┘ └─────────┘ └──┬───┘  │
│           │                                                         │      │
│  ┌────────▼─────────┐                                              │      │
│  │  SFCaseUpdater   │◄─── (close case after success)               │      │
│  └──────────────────┘                                              │      │
│                                                                     │      │
│  ┌──────────────────┐                                              │      │
│  │  API Server      │ ← localhost:5000 (for UI)                    │      │
│  │  (api_server.py) │                                              │      │
│  └──────────────────┘                                              │      │
└─────────────┬───────────────────────────────────────────────────────┼──────┘
              │                                                       │
              ▼                                                       ▼
  ┌───────────────────────┐                          ┌──────────────────────────┐
  │  Salesforce Sandbox   │                          │  Mobius Gateway API      │
  │  cardxscb--uat        │                          │  kong-uat2-pci-clb       │
  │  • Case extraction    │                          │  • GET profile/List      │
  │  • Case closure       │                          │  • PUT cust-profile      │
  └───────────────────────┘                          │  • POST address          │
                                                     │  • POST Contacts         │
              ┌──────────────────┐                   └──────────────────────────┘
              │  Call Center UI  │
              │  (HTML/CSS/JS)   │
              │  • Agent workflow │
              │  • Approval queue │
              │  • Audit log     │
              │  • CEO Dashboard │
              └──────────────────┘
```

### Pipeline Flow (main.py)

```
Extract SF Cases ──> Analyze Intent ──> Validate Docs ──> Update Local Store
                                                                │
                                                                ▼
                                              Sync to Mobius (best-effort)
                                                                │
                                                                ▼
                                              Close SF Case (Status=Closed)
                                                                │
                                                                ▼
                                              Log Summary (completed/skipped/failed/synced)
```

### Technology Stack
- **Language**: Python 3.11+
- **HTTP Client (SF)**: `simple_salesforce==1.12.5` — Salesforce REST API / SOQL
- **HTTP Client (Mobius)**: `requests==2.32.3` — Mobius Gateway API
- **Local Storage**: JSON file (`data/customer_data.json`) with `filelock==3.13.1`
- **Configuration**: `.env` file via `python-dotenv==1.0.1`
- **Testing**: `pytest==8.2.0` + `pytest-mock==3.14.0`
- **UI**: Static HTML/CSS/JS — Tesseract.js 5.1.1 (OCR), Chart.js 4.4.3 (dashboard)
- **API Server**: Python `http.server` (stdlib) on localhost:5000

### Key Design Decisions

1. **Strategy Pattern for Intent Registry**: Each intent processor implements `IntentProcessor` ABC (validate + process). Registered by exact `Type__c` string. Adding a new intent to `INTENT_FIELD_MAP` auto-registers it everywhere.

2. **Dual-filter SOQL at query time**: Uses `Type__c LIKE 'CC - ข้อมูลส่วนตัว%'` AND `Status != 'Closed'` — reduces data transfer and enforces scope at source. Prefix list auto-generated from `INTENT_FIELD_MAP` keys.

3. **Per-case error isolation**: Each case processed in try/except. One failure logs and continues — does not halt pipeline for other cases.

4. **Mobius best-effort sync**: Local CustomerDataStore update is the source of truth. Mobius sync happens after local success. If Mobius fails, local update and SF closure still proceed.

5. **SF Case auto-closure**: After successful processing + Mobius sync attempt, the pipeline closes the SF case (Status=Closed, Sub_Status__c=Done) to keep the queue clean.

6. **Citizen ID as universal key**: CID (Process_Add_Info_9__c) is used to look up customers in both local store and Mobius (`GET /customer/profile/List?idNumber={cid}`).

7. **Title code mapping**: Thai titles (นาย, นาง, นางสาว) are mapped to Mobius codes (MR., MRS., MISS) via `mobius_client/models.py`.

## Salesforce Field Mapping

| Salesforce Field | SFCase Property | Purpose |
|---|---|---|
| Id | case_id | Unique case identifier |
| CaseNumber | case_number | Human-readable case number |
| Subject | subject | Full intent string |
| Type__c | intent_type / intent_name | Intent routing key |
| Status | status | Case status (Open, In Progress, Closed) |
| Sub_Status__c | sub_status | Sub-status for closure |
| Category__c | category | Case category |
| Customer_Name__c | customer_name | Customer display name |
| Process_Add_Info_1__c | new_first_name | New first name / address / phone / email |
| Process_Add_Info_2__c | new_last_name | New last name |
| Process_Add_Info_3__c | new_title | New title/prefix |
| Process_Add_Info_4__c | old_name | Previous name |
| Process_Add_Info_9__c | citizen_id / cid | Citizen ID (13-digit) |
| ContactId | contact_id | SF Contact reference |
| AccountId | account_id | SF Account reference |

## Mobius API Integration

### Authentication Headers
```
MBS-Authorization: Basic Q0JTOjEyMzQ1Njc4OTA=
Authorization: Basic Y2R4LXVhdDItcGNpLWNpOjREa3EzQlZDVG1UQXFhNTNwbTZmMVE5bWFWY0p2TFZMSUNqeE4xMVY=
channelCode: CCRS
requestUID: {uuid4}
correlationID: {uuid4}
```

### Endpoints

| Method | Path | Purpose | Request Body |
|--------|------|---------|-------------|
| GET | `/customer/profile/List?searchBy=ID_NUMBER&idNumber={cid}&idType=P1` | Search CIF by citizen ID | — |
| PUT | `/party/cust-profile` | Update name/title | `{customerId, titleCode?, thaiFirstName?, thaiLastName?}` |
| POST | `/party/cust-profile/address` | Update address | `{customerId, addressFormat, addressType, addressNumber, moo, soi, ...}` |
| POST | `/party/cust-profile/{cif}/Contacts` | Update phone/email | `{customerId, contactTypeCode, contactInformation, contactCategory}` |

### Contact Type Codes
- `PM` = Primary Mobile Phone
- `PE` = Primary Email

### Title Code Mapping
| Thai | Mobius Code |
|------|------------|
| นาย | MR. |
| นาง | MRS. |
| นางสาว | MISS |
| เด็กชาย | MAST |
| เด็กหญิง | MISS |

## Traceability

| Requirement | Component(s) | Data Entity | Integration |
|---|---|---|---|
| R1: Extract non-closed CIU cases | SFCaseExtractor, SOQL Builder | SFCase, VerificationDocument | Salesforce SOQL |
| R2: Intent classification & routing | IntentAnalyzer, IntentRegistry, field_map.py | SFCase, ProcessingResult | — |
| R3: Mobius API sync | MobiusClient | MobiusResult | Mobius Gateway (GET/PUT/POST) |
| R4: SF case closure | SFCaseUpdater | SFCase | Salesforce Case.update() |
| R5: Document validation | DocumentValidator | VerificationDocument | — |
| R6: Call Center UI | index.html, app.js, db.js, ocr.js | — | localhost:5000 API |
| R7: Executive Dashboard | dashboard.html, dashboard.js | — | localStorage events |
| R8: API Server | api_server.py | SFCase | Salesforce SOQL |
| R9: Extensible intents | INTENT_FIELD_MAP, IntentRegistry | — | — |

## Open Questions & Risks

| # | Question/Risk | Impact | Status |
|---|--------------|--------|--------|
| 1 | Mobius API credentials are hardcoded for UAT — need rotation strategy for production | Medium | Open |
| 2 | Address update currently passes full address string in `addressNumber` field — needs proper field parsing | Low | Known limitation |
| 3 | Phone/Email stored in Process_Add_Info_1__c (same field) — relies on intent routing to disambiguate | Low | By design |
| 4 | No Mobius unit tests yet (tasks 9.5, 9.6 pending) | Medium | Open |
| 5 | Jira integration module is placeholder only (Phase 10 not started) | Low | Deferred |

## Detailed Specifications

- [Components](design/components.md) — component breakdown and interfaces
- [Data Model](design/data-model.md) — entities, relationships, schemas
- [Integration](design/integration.md) — Salesforce + Mobius API integration
- [Implementation](design/implementation.md) — directory structure, setup, conventions
- [Non-Functional Requirements](design/nfr.md) — retry, timeout, error isolation

## External References

| Source | Type | Used in |
|--------|------|---------|
| Salesforce Sandbox (cardxscb--uat) | Live API | SFCaseExtractor, SFCaseUpdater, APIServer |
| Mobius Gateway UAT (kong-uat2-pci-clb.int-np.cardx.co.th) | Live API | MobiusClient |
| Tesseract.js CDN | JS Library | OCR verification in UI |
| Chart.js CDN | JS Library | Dashboard charts |
