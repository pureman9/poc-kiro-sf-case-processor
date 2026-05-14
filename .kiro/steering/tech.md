---
inclusion: always
---

# Technology Context

## Summary
- **Stack**: Python 3.11+ / simple_salesforce / JSON file store
- **Architecture**: Modular Monolith — sequential pipeline with Strategy pattern for intent processors
- **Infra**: Local execution (no cloud required)

## Stack

- **Languages**: Python 3.11+
- **Frameworks**: None (CLI/batch runner — no web framework)
- **Build System**: pip + venv
- **Package Manager**: pip
- **Testing**: pytest + pytest-mock

## Architecture

- **Pattern**: Modular Monolith — pipeline runner orchestrates self-contained modules (SFCaseExtractor → IntentAnalyzer → IntentProcessor → DocumentValidator → CustomerDataStore)
- **API Style**: N/A — batch processing pipeline, not a web API

## Infrastructure

- **Cloud Provider**: None — local execution
- **Compute**: Local process (CLI / scheduled task)
- **Database**: Local JSON file (`customer_data.json`) keyed by CID
- **IaC Tool**: None

## Patterns & Conventions

- **Architecture pattern**: Modular Monolith — each domain is a self-contained Python module; pipeline runner in `main.py` orchestrates them
- **Intent Registry**: Strategy pattern — `IntentProcessor` ABC with `validate()` + `process()` methods; `IntentRegistry` maps intent name strings to processor instances
- **Data access**: Direct JSON file I/O with `filelock` for atomic read-modify-write
- **Error handling**: Per-case try/except isolation; only `ExtractionError` and `StorageInitError` halt the pipeline
- **Retry logic**: Fixed 2s delay, up to 3 retries for Salesforce queries; 30s timeout per attempt
- **Logging**: Structured JSON logging via custom `JsonFormatter`; PII (field values) never logged
- **Code style**: PEP 8; snake_case files/functions, PascalCase classes, UPPER_SNAKE_CASE constants
- **Naming conventions**: snake_case for files and functions, PascalCase for classes

## Environment Configuration

- **Config approach**: `python-dotenv` — `.env` file per environment, never committed
- **Environments**: local / sandbox (SF_DOMAIN=test) / production (SF_DOMAIN=login)
- **Secrets management**: `.env` file (not committed); `.env` in `.gitignore`

## CI/CD Pipeline

- **Tool**: None configured — manual execution
- **Stages**: N/A
- **Deploy target**: Local / scheduled task

## Dependency Management

- **Lockfile**: `requirements.txt` with pinned versions
- **Version strategy**: Exact pinned versions (`==`)
- **Monorepo tooling**: N/A — single repo
