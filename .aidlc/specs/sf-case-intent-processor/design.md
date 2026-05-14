# Design Document: SF Case Intent Processor

## Summary
- **Architecture**: Pipeline / Modular Monolith — sequential processing stages with pluggable intent processors via Strategy pattern
- **Stack**: Python 3.11+ / No web framework (CLI/batch runner) / JSON file store (local) / No cloud infra required
- **Components**: 5 — SFCaseExtractor, IntentAnalyzer, IntentRegistry, DocumentValidator, CustomerDataStore
- **Entities**: 4 — SFCase, VerificationDocument, CustomerRecord, ProcessingResult
- **Integrations**: 1 — Salesforce REST API (SOQL query)
- **Testing**: PBT No — NFR Yes (retry, timeout, per-case isolation)
- **Key Decisions**: Python pipeline runner, Strategy pattern for intent registry, JSON file as local Customer_Data_Store

## Architecture

### System Context Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    SF Case Intent Processor                      │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │  SFCaseExtractor │───>│  IntentAnalyzer  │                   │
│  │  (Salesforce     │    │  + IntentRegistry│                   │
│  │   SOQL query)    │    │  (Strategy)      │                   │
│  └──────────────────┘    └────────┬─────────┘                   │
│                                   │                              │
│                    ┌──────────────▼──────────────┐              │
│                    │  PersonalInfoChangeProcessor │              │
│                    │  ┌──────────────────────┐   │              │
│                    │  │  DocumentValidator   │   │              │
│                    │  └──────────┬───────────┘   │              │
│                    │             │               │              │
│                    │  ┌──────────▼───────────┐   │              │
│                    │  │  CustomerDataStore   │   │              │
│                    │  └──────────────────────┘   │              │
│                    └─────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
         │                                          │
         ▼                                          ▼
  ┌─────────────┐                         ┌──────────────────┐
  │  Salesforce │                         │  Local JSON File │
  │  REST API   │                         │  (customer_data) │
  └─────────────┘                         └──────────────────┘
```

### Technology Stack
- **Language**: Python 3.11+
- **HTTP Client**: `simple_salesforce` library for Salesforce API
- **Local Storage**: JSON file (`customer_data.json`) — keyed by CID
- **Logging**: Python `logging` module with structured output (JSON formatter)
- **Configuration**: `.env` file via `python-dotenv`
- **Testing**: `pytest` + `pytest-mock`
- **Key Libraries**: `simple_salesforce`, `python-dotenv`, `pytest`

### Key Design Decisions
1. **Strategy Pattern for Intent Registry**: Each intent processor is a class implementing `IntentProcessor` interface (validate + process methods). Registered by exact intent name string. Enables Requirement 6 (extensibility) without modifying existing code.
2. **Dual-filter at query time**: Salesforce SOQL query filters both `Status != 'Closed'` AND intent name matches Customer Information Update category — reduces data transfer and enforces Requirement 1 scope at the source.
3. **Per-case error isolation**: Each case is processed in a try/except block. One case failure logs and continues — does not halt the pipeline for other cases.
4. **JSON file as Customer_Data_Store**: Simple, no-dependency local storage. Keyed by CID. Atomic read-modify-write with file locking to prevent corruption.

## Traceability

| Requirement | Component(s) | Data Entity | Design File |
|---|---|---|---|
| R1: Extract non-closed CIU cases | SFCaseExtractor | SFCase | components.md, integration.md |
| R2: Identify sub-intent | IntentAnalyzer, IntentRegistry | SFCase | components.md |
| R3: Analyze by sub-intent | IntentAnalyzer, IntentRegistry, PersonalInfoChangeProcessor | SFCase, ProcessingResult | components.md |
| R4: Validate verification document | DocumentValidator | VerificationDocument | components.md, data-model.md |
| R5: Update customer data | CustomerDataStore | CustomerRecord | components.md, data-model.md |
| R6: Extensible intent processing | IntentRegistry | — | components.md |

## Open Questions & Risks

| # | Question/Risk | Impact | Status |
|---|--------------|--------|--------|
| 1 | Salesforce API credentials and org URL must be provided via env vars — not yet confirmed | High | Open |
| 2 | Exact SOQL field name for "intent name" in Salesforce schema not confirmed — assumed `Intent_Name__c` (custom field) | High | Open |
| 3 | Exact intent name strings for all Customer Information Update sub-intents not fully enumerated — only one example given in requirements | Medium | Open |
| 4 | File locking strategy for `customer_data.json` under concurrent runs not tested | Medium | Open |

## Detailed Specifications

- [Components](design/components.md) — component breakdown and interfaces
- [Data Model](design/data-model.md) — entities, relationships, schemas
- [Integration](design/integration.md) — Salesforce API integration
- [Implementation](design/implementation.md) — directory structure, setup, conventions
- [Non-Functional Requirements](design/nfr.md) — retry, timeout, error isolation

## External References

| Source | Type | Used in |
|--------|------|---------|
| d:\POC-Kiro\requirements.md | Requirements | All design files |
