"""Shared test fixtures for the SF Case Intent Processor test suite."""

import json
import pytest
from pathlib import Path


# ── Test case marker ───────────────────────────────────────────────────────────
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "tc(id): link test to a test case ID (e.g., @pytest.mark.tc('TC-001'))")


# ── Sample customer data fixture ───────────────────────────────────────────────
SAMPLE_CUSTOMERS = {
    "C001234": {
        "cid": "C001234",
        "title": "นาย",
        "first_name": "สมชาย",
        "last_name": "ใจดี",
        "national_id": "1100100012345",
        "dob": "1985-03-15",
        "phone": "081-234-5678",
        "email": "somchai@email.com",
    },
    "C002345": {
        "cid": "C002345",
        "title": "นาง",
        "first_name": "สมหญิง",
        "last_name": "รักดี",
        "national_id": "1100200023456",
        "dob": "1990-07-22",
        "phone": "082-345-6789",
        "email": "somying@email.com",
    },
}


@pytest.fixture
def customer_data_file(tmp_path: Path) -> Path:
    """Create a temporary customer_data.json file with sample data."""
    data_file = tmp_path / "customer_data.json"
    data_file.write_text(json.dumps(SAMPLE_CUSTOMERS, ensure_ascii=False, indent=2), encoding="utf-8")
    return data_file


@pytest.fixture
def empty_customer_data_file(tmp_path: Path) -> Path:
    """Create a temporary empty customer_data.json file."""
    data_file = tmp_path / "customer_data.json"
    data_file.write_text("{}", encoding="utf-8")
    return data_file
