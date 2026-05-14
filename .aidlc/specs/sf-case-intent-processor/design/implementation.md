# Implementation Specifications

## Code Organization

**Architecture Pattern**: Modular Monolith — each domain component is a self-contained module with clear boundaries. The pipeline runner orchestrates them.
**Repository**: Single repo

### Directory Structure

```
sf-case-intent-processor/
├── main.py                          # Pipeline runner entry point
├── config.py                        # Environment config loader (dotenv)
├── requirements.txt                 # Python dependencies (pinned versions)
├── .env.example                     # Template for environment variables
├── data/
│   └── customer_data.json           # Local customer record store
│
├── sf_case_extractor/
│   ├── __init__.py
│   ├── extractor.py                 # SFCaseExtractor class
│   ├── soql_builder.py              # Builds SOQL query string
│   └── models.py                    # SFCase, VerificationDocument dataclasses
│
├── intent_analyzer/
│   ├── __init__.py
│   ├── analyzer.py                  # IntentAnalyzer class
│   ├── registry.py                  # IntentRegistry class
│   ├── base_processor.py            # IntentProcessor ABC
│   └── exceptions.py                # MissingIntentError, UnrecognizedIntentError, RegistrationError
│
├── document_validator/
│   ├── __init__.py
│   ├── validator.py                 # DocumentValidator class
│   └── models.py                    # ValidationResult dataclass
│
├── customer_data_store/
│   ├── __init__.py
│   ├── store.py                     # CustomerDataStore class
│   └── models.py                    # CustomerRecord, UpdateResult dataclasses
│
├── intents/
│   ├── __init__.py
│   └── personal_info_change/
│       ├── __init__.py
│       ├── processor.py             # PersonalInfoChangeProcessor class
│       └── field_map.py             # Intent name → field name mapping dict
│
├── shared/
│   ├── __init__.py
│   ├── models.py                    # ProcessingResult, ProcessingStatus shared types
│   ├── logger.py                    # Structured JSON logger setup
│   └── exceptions.py                # ExtractionError, StorageInitError, CIDNotFoundError
│
└── tests/
    ├── conftest.py                  # Shared fixtures (mock SF client, temp JSON file)
    ├── unit/
    │   ├── test_extractor.py
    │   ├── test_intent_analyzer.py
    │   ├── test_intent_registry.py
    │   ├── test_document_validator.py
    │   ├── test_customer_data_store.py
    │   └── test_personal_info_processor.py
    └── integration/
        └── test_pipeline.py         # End-to-end pipeline test with mocked SF
```

### Module Boundaries
- `main.py` orchestrates the pipeline — it imports from all modules but modules do NOT import from each other except through defined interfaces
- `intent_analyzer` imports `base_processor.py` interface only — it does NOT import concrete processors
- Concrete processors (in `intents/`) import `document_validator` and `customer_data_store`
- `shared/` is the only cross-cutting module — all others may import from it
- No circular imports allowed

### Naming Conventions
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Dataclass fields**: `snake_case`

---

## Technology Stack

### Dependencies (`requirements.txt`)
```
simple-salesforce==1.12.5
python-dotenv==1.0.1
filelock==3.13.1
pytest==8.2.0
pytest-mock==3.14.0
```

> All versions pinned for reproducibility.

---

## Development Setup

### Prerequisites
- Python 3.11+
- pip

### Setup Commands
```bash
# Clone and set up
git clone <repo-url>
cd sf-case-intent-processor

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your Salesforce credentials and data path
```

### Environment Variables (`.env`)
| Variable | Description | Example |
|---|---|---|
| `SF_USERNAME` | Salesforce login username | `operator@company.com` |
| `SF_PASSWORD` | Salesforce login password | `[your password]` |
| `SF_SECURITY_TOKEN` | Salesforce security token | `[your token]` |
| `SF_DOMAIN` | Salesforce domain | `login` (prod) or `test` (sandbox) |
| `CUSTOMER_DATA_PATH` | Path to customer JSON file | `./data/customer_data.json` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Running the Pipeline
```bash
python main.py
```

### Running Tests
```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# With coverage
pytest --cov=. --cov-report=term-missing
```

---

## Pipeline Runner (`main.py`)

```python
"""
SF Case Intent Processor — Pipeline Runner
"""
import logging
from config import load_config
from sf_case_extractor.extractor import SFCaseExtractor
from intent_analyzer.analyzer import IntentAnalyzer
from intent_analyzer.registry import IntentRegistry
from document_validator.validator import DocumentValidator
from customer_data_store.store import CustomerDataStore
from intents.personal_info_change.processor import PersonalInfoChangeProcessor
from shared.exceptions import ExtractionError, StorageInitError

def build_registry(doc_validator, data_store) -> IntentRegistry:
    """Register all known intent processors."""
    registry = IntentRegistry()
    processor = PersonalInfoChangeProcessor(doc_validator, data_store)
    
    # Register all known Customer Information Update intent name strings
    for intent_name in PersonalInfoChangeProcessor.SUPPORTED_INTENTS:
        registry.register(intent_name, processor)
    
    return registry

def run():
    config = load_config()
    logger = logging.getLogger(__name__)
    
    # Initialize components
    extractor = SFCaseExtractor(config)
    doc_validator = DocumentValidator()
    data_store = CustomerDataStore(config.customer_data_path)
    registry = build_registry(doc_validator, data_store)
    analyzer = IntentAnalyzer(registry)
    
    # Extract cases
    try:
        cases = extractor.extract()
    except ExtractionError as e:
        logger.error(f"Pipeline aborted: extraction failed — {e}")
        return
    except StorageInitError as e:
        logger.error(f"Pipeline aborted: storage init failed — {e}")
        return
    
    logger.info(f"Extracted {len(cases)} cases for processing")
    
    # Process each case (per-case error isolation)
    results = []
    for case in cases:
        result = analyzer.analyze(case)
        results.append(result)
        logger.info(f"Case {case.case_id}: {result.status.value} — {result.reason or result.field_updated or ''}")
    
    # Summary
    completed = sum(1 for r in results if r.status.value == "COMPLETED")
    skipped   = sum(1 for r in results if r.status.value == "SKIPPED")
    failed    = sum(1 for r in results if r.status.value == "FAILED")
    logger.info(f"Pipeline complete — {completed} completed, {skipped} skipped, {failed} failed")

if __name__ == "__main__":
    run()
```

---

## Logging

**Format**: Structured JSON (one JSON object per log line) for easy parsing.

**Logger Setup** (`shared/logger.py`):
```python
import logging
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "case_id"):
            log_obj["case_id"] = record.case_id
        if hasattr(record, "cid"):
            log_obj["cid"] = record.cid
        return json.dumps(log_obj, ensure_ascii=False)
```

**Log Events**:
| Event | Level | Fields |
|---|---|---|
| Extraction started | INFO | — |
| Extraction succeeded | INFO | case_count |
| Extraction failed (retry) | WARNING | attempt, error |
| Extraction failed (final) | ERROR | error |
| Case: missing intent | WARNING | case_id, reason |
| Case: unrecognized intent | WARNING | case_id, intent_name |
| Case: no document | WARNING | case_id |
| Case: invalid document | WARNING | case_id, doc_id, doc_status |
| Case: validation failed | WARNING | case_id, intent_name, reason |
| Case: CID not found | ERROR | case_id, cid |
| Case: storage error | ERROR | case_id, cid, operation, error |
| Case: completed | INFO | case_id, cid, field_updated |
| Pipeline summary | INFO | completed, skipped, failed |

---

## Testing

**Unit Tests**: `pytest` — `pytest tests/unit/`
**Integration Tests**: `pytest` — `pytest tests/integration/`
**Coverage Target**: 80%+ overall, 100% on DocumentValidator and CustomerDataStore (critical business logic)
