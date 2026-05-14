# Context Assessment

## Summary
- **Type**: Greenfield (implemented)
- **Stack**: Python 3.11+ / simple_salesforce / requests / JSON file store + HTML/CSS/JS Call Center UI
- **Architecture**: Modular Monolith — sequential pipeline with Strategy pattern for intent processors + browser-based UI with real-time dashboard
- **Feature**: SF Case Intent Processor — extracts Salesforce cases, identifies intent, validates documents, updates customer data, syncs to Mobius API, and closes SF cases
- **Impact**: Full end-to-end system with real Salesforce sandbox + Mobius API integration
- **Complexity**: High — 7 intents (5 with Mobius sync), 6 domains, 2 external integrations (Salesforce + Mobius), browser UI + executive dashboard
- **Recommendations**: Personas No, Units Yes, NFR Yes

## Project Overview
- **Type**: Greenfield (fully implemented)
- **Assessment Date**: 2025-01-15T00:00:00Z

## Technology Stack
- **Languages**: Python 3.11+, JavaScript (ES6+), HTML5, CSS3
- **Frameworks**: None (Python CLI/batch runner + static HTML/CSS/JS UI)
- **Build System**: pip + venv (Python), no build step (JS)
- **Testing**: pytest + pytest-mock (84 unit + integration tests)
- **Infrastructure**: Local execution — Python pipeline + localhost:5000 API server
- **Key Libraries**:
  - `simple-salesforce==1.12.5` — Salesforce REST API / SOQL
  - `python-dotenv==1.0.1` — Environment configuration
  - `filelock==3.13.1` — Atomic JSON file writes
  - `requests==2.32.3` — Mobius API HTTP client
  - `pytest==8.2.0` / `pytest-mock==3.14.0` — Testing
  - `Tesseract.js 5.1.1` — Browser-side OCR (Thai + English)
  - `Chart.js 4.4.3` — Dashboard charts

## Patterns & Conventions
- **Architecture**: Modular Monolith — pipeline runner (`main.py`) orchestrates self-contained modules
- **Intent Registry**: Strategy pattern — `IntentProcessor` ABC with `validate()` + `process()` methods; `IntentRegistry` maps intent name strings to processor instances
- **Field Map**: Extensible `INTENT_FIELD_MAP` dict in `field_map.py` — adding a new intent auto-registers it in SOQL queries, processing, and routing
- **Data access**: JSON file I/O with `filelock` for atomic read-modify-write (backend); localStorage (UI)
- **Error handling**: Per-case try/except isolation; only `ExtractionError` and `StorageInitError` halt the pipeline
- **Retry logic**: Fixed 2s delay, up to 3 retries for Salesforce queries; 30s timeout per Mobius API call with 3 retries
- **Logging**: Structured JSON logging via custom `JsonFormatter`; PII (field values) never logged
- **Code style**: PEP 8; snake_case files/functions, PascalCase classes, UPPER_SNAKE_CASE constants
- **Mobius sync**: Best-effort — local update succeeds even if Mobius call fails

## Codebase Analysis

### Backend (`sf-case-intent-processor/`)
| Module | Purpose | Key Files |
|--------|---------|-----------|
| `sf_case_extractor/` | Salesforce SOQL query + case parsing | `extractor.py`, `soql_builder.py`, `case_updater.py`, `models.py` |
| `intent_analyzer/` | Intent identification + processor routing | `analyzer.py`, `registry.py`, `base_processor.py` |
| `document_validator/` | Verification document validation | `validator.py`, `models.py` |
| `customer_data_store/` | Local JSON storage read/write | `store.py`, `models.py` |
| `intents/personal_info_change/` | All CIU intent processing | `processor.py`, `field_map.py` |
| `mobius_client/` | Mobius API integration (search + update) | `client.py`, `models.py` |
| `shared/` | Cross-cutting types, logger, exceptions | `models.py`, `logger.py`, `exceptions.py` |
| `tests/` | 84 unit + integration tests | `unit/` (8 test files), `integration/` (1 test file) |

### Frontend (`Case_Update_Name/`)
| File | Purpose |
|------|---------|
| `index.html` | Call Center Agent UI — 4-step case processing workflow |
| `app.js` | Intent definitions, form logic, approval routing, SF case refresh |
| `db.js` | localStorage-based customer database + audit log |
| `ocr.js` | Tesseract.js OCR verification (Thai ID card) |
| `dashboard.html` | Executive Operations Dashboard |
| `dashboard.js` | KPI calculations, Chart.js charts, auto-refresh |
| `styles.css` | Salesforce Lightning-inspired UI theme |
| `dashboard.css` | Dark theme dashboard styles |

### Entry Points
| Entry Point | Type | Description |
|-------------|------|-------------|
| `main.py` | CLI / batch runner | Full pipeline: Extract → Analyze → Validate → Update → Mobius Sync → Close SF Case |
| `api_server.py` | HTTP server (localhost:5000) | REST API for UI to query live SF cases |
| `sync_to_ui.py` | CLI script | One-shot sync SF cases to `sf_cases_data.js` for offline UI |
| `index.html` | Browser UI | Call center agent workflow (open directly in browser) |
| `dashboard.html` | Browser UI | Executive dashboard with KPIs and charts |

## Feature Impact

**Affected Areas**: Full standalone system — Salesforce sandbox + Mobius UAT + browser UI

| Area | Impact | Reason |
|------|--------|--------|
| SF_Case_Extractor | Implemented | Queries real Salesforce sandbox (cardxscb--uat) for CIU cases |
| Intent_Analyzer | Implemented | Routes 7 intent types to PersonalInfoChangeProcessor |
| Document_Validator | Implemented | Validates attached documents; skips for phone/email/address intents |
| Customer_Data_Store | Implemented | JSON file store with filelock; localStorage in UI |
| Mobius_Client | Implemented | Real integration with kong-uat2-pci-clb.int-np.cardx.co.th |
| SF_Case_Updater | Implemented | Closes SF cases (Status=Closed, Sub_Status__c=Done) after processing |
| Call_Center_UI | Implemented | Full 4-step workflow with OCR, approval queue, audit log |
| Executive_Dashboard | Implemented | KPIs, charts, auto-refresh, dark theme |
| API_Server | Implemented | localhost:5000 — bridges UI to live Salesforce data |

## External Integrations

| System | Environment | Base URL | Purpose |
|--------|-------------|----------|---------|
| Salesforce | Sandbox (UAT) | cardxscb--uat.sandbox.my.salesforce.com | Case extraction + closure |
| Mobius API | UAT | kong-uat2-pci-clb.int-np.cardx.co.th/sde-biz-cardx-mobius-gateway-ws/v1 | Customer profile search + update |

### Mobius API Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/customer/profile/List` | Search CIF by citizen ID (idType=P1) |
| PUT | `/party/cust-profile` | Update name/title (titleCode, thaiFirstName, thaiLastName) |
| POST | `/party/cust-profile/address` | Update customer address |
| POST | `/party/cust-profile/{cif}/Contacts` | Update phone (PM) or email (PE) |

## Recommendations

- Story Count: High (9 requirements implemented)
- Domain Boundaries: 6 distinct domains — SF extraction, intent routing, document validation, customer data persistence, Mobius sync, UI/dashboard
- User Types: 3 (call center agent, reviewer/ops team, executive/CEO)
- Integration Points: 2 (Salesforce REST API, Mobius Gateway API)
- **Personas**: No — technical user types with clear roles
- **Units**: Yes — 6 clear domain boundaries
- **NFR**: Yes — retry logic, timeout requirements, per-case isolation, atomic writes, real-time dashboard refresh

## Recommended Workflow

```
       ┌─────────────┐
       │  Context ✅  │
       └──────┬──────┘
              ▼
       ┌──────────────┐
       │Requirements ✅│
       └──────┬───────┘
              ▼
       ┌───────────────┐
       │   Design ✅    │
       └───────┬───────┘
               ▼
    ┌──────────┬──────────┬──────────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│SF Extr.│ │Intent  │ │Doc Val.│ │Cust.DS │ │Mobius  │ │  UI    │
│  ✅    │ │  ✅    │ │  ✅    │ │  ✅    │ │  ✅    │ │  ✅    │
└───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
    │          │          │          │          │          │
    └──────────┴──────────┴──────────┴──────────┴──────────┘
                              ▼
                   ┌──────────────────┐
                   │  Pipeline ✅      │
                   │  (main.py)       │
                   └────────┬─────────┘
                            ▼
                   ┌─────────────────┐
                   │  Tests ✅ (84)   │
                   └─────────────────┘
```

## External References

| Source | Type | What was used |
|--------|------|---------------|
| Salesforce Sandbox | Live API | cardxscb--uat — real case extraction and closure |
| Mobius Gateway UAT | Live API | kong-uat2-pci-clb.int-np.cardx.co.th — customer profile CRUD |
| d:\POC-Kiro\requirements.md | Requirements | Original requirements document |
