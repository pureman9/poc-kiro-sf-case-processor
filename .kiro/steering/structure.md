---
inclusion: always
---

# Project Structure

## Summary
- **Repo**: Single repo
- **Source**: `sf_case_extractor/`, `intent_analyzer/`, `document_validator/`, `customer_data_store/`, `intents/`, `shared/`
- **Entry**: `main.py` — pipeline runner

## Repository

- **Type**: Single repo
- **Root**: `sf-case-intent-processor/` — Python project with modular structure

## Key Directories

| Directory | Purpose | Key Contents |
|-----------|---------|-------------|
| `sf_case_extractor/` | Salesforce query and case retrieval | `extractor.py`, `soql_builder.py`, `models.py` |
| `intent_analyzer/` | Intent identification and processor registry | `analyzer.py`, `registry.py`, `base_processor.py` |
| `document_validator/` | Verification document validation | `validator.py`, `models.py` |
| `customer_data_store/` | Local JSON storage read/write | `store.py`, `models.py` |
| `intents/` | Registered intent processor implementations | `personal_info_change/processor.py`, `field_map.py` |
| `shared/` | Cross-cutting types, logger, exceptions | `models.py`, `logger.py`, `exceptions.py` |
| `data/` | Local data files | `customer_data.json` |
| `tests/` | Unit and integration tests | `unit/`, `integration/`, `conftest.py` |

## Key Files

| File | Purpose | Notes |
|------|---------|-------|
| `main.py` | Pipeline runner entry point | Orchestrates all components |
| `config.py` | Environment config loader | Uses `python-dotenv` |
| `requirements.txt` | Python dependencies | All versions pinned with `==` |
| `.env.example` | Environment variable template | Copy to `.env`, fill credentials |
| `data/customer_data.json` | Customer record store | JSON object keyed by CID |

## Entry Points

| Entry Point | Type | Description |
|-------------|------|-------------|
| `main.py` | CLI / batch runner | Runs the full pipeline: extract → analyze → validate → update |

## Module Dependencies

```
main.py
  → sf_case_extractor/extractor.py
  → intent_analyzer/analyzer.py
      → intent_analyzer/registry.py
          → intent_analyzer/base_processor.py (ABC)
  → intents/personal_info_change/processor.py
      → document_validator/validator.py
      → customer_data_store/store.py
  → shared/ (all modules)
```

Key dependency rules:
- `intent_analyzer` imports `base_processor.py` interface only — never imports concrete processors
- Concrete processors in `intents/` import `document_validator` and `customer_data_store`
- `shared/` is the only cross-cutting module — all others may import from it
- No circular imports allowed
