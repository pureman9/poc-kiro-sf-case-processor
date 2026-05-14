"""Integration tests for the full pipeline: extract → analyze → validate → update."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from config import AppConfig
from sf_case_extractor.extractor import SFCaseExtractor
from sf_case_extractor.models import SFCase, VerificationDocument
from intent_analyzer.analyzer import IntentAnalyzer
from intent_analyzer.registry import IntentRegistry
from document_validator.validator import DocumentValidator
from customer_data_store.store import CustomerDataStore
from intents.personal_info_change.processor import PersonalInfoChangeProcessor
from intents.personal_info_change.field_map import SUPPORTED_INTENTS
from shared.models import ProcessingStatus
from shared.exceptions import ExtractionError


SAMPLE_CUSTOMERS = {
    "9280635310483": {
        "cid": "9280635310483",
        "title": "นาย",
        "first_name": "ปิติกรณ์",
        "last_name": "ใจดี",
        "phone": "081-234-5678",
        "email": "test@email.com",
        "address": "123 ถนนสุขุมวิท",
    },
    "1234567890123": {
        "cid": "1234567890123",
        "title": "นาง",
        "first_name": "สมหญิง",
        "last_name": "รักดี",
        "phone": "082-345-6789",
        "email": "somying@email.com",
        "address": "456 ถนนพหลโยธิน",
    },
}


@pytest.fixture
def data_file(tmp_path: Path) -> Path:
    f = tmp_path / "customer_data.json"
    f.write_text(json.dumps(SAMPLE_CUSTOMERS, ensure_ascii=False, indent=2), encoding="utf-8")
    return f


@pytest.fixture
def pipeline(data_file):
    """Set up the full pipeline with mocked Salesforce."""
    doc_validator = DocumentValidator()
    data_store = CustomerDataStore(str(data_file))
    registry = IntentRegistry()
    processor = PersonalInfoChangeProcessor(doc_validator, data_store)

    for intent_name in SUPPORTED_INTENTS:
        registry.register(intent_name, processor)

    analyzer = IntentAnalyzer(registry)
    return analyzer, data_store, data_file


class TestFullPipeline:
    """End-to-end pipeline tests with mocked Salesforce extraction."""

    def test_valid_name_change_case(self, pipeline):
        """Valid case with document → customer record updated."""
        analyzer, data_store, _ = pipeline

        case = SFCase(
            case_id="CASE-001",
            case_number="00163523",
            subject="ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล",
            intent_type="CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล",
            status="Open",
            citizen_id="9280635310483",
            new_first_name="ดารุณี",
            new_last_name="อะฟาฟ",
            verification_documents=[
                VerificationDocument(doc_id="DOC-1", name="id_card.pdf", size_bytes=50000),
            ],
        )

        result = analyzer.analyze(case)

        assert result.status == ProcessingStatus.COMPLETED
        assert "first_name" in result.field_updated
        assert "last_name" in result.field_updated

        # Verify DB updated
        record = data_store.get("9280635310483")
        assert record["first_name"] == "ดารุณี"
        assert record["last_name"] == "อะฟาฟ"
        assert record["title"] == "นาย"  # unchanged

    def test_missing_intent_case(self, pipeline):
        """Case with empty intent → SKIPPED."""
        analyzer, data_store, _ = pipeline

        case = SFCase(
            case_id="CASE-002",
            case_number="00163524",
            subject="",
            intent_type="",
            status="Open",
            citizen_id="9280635310483",
        )

        result = analyzer.analyze(case)
        assert result.status == ProcessingStatus.SKIPPED
        assert result.reason == "MISSING_INTENT"

        # DB unchanged
        record = data_store.get("9280635310483")
        assert record["first_name"] == "ปิติกรณ์"

    def test_no_document_case(self, pipeline):
        """Case requiring doc but none attached → SKIPPED (validation failed)."""
        analyzer, data_store, _ = pipeline

        case = SFCase(
            case_id="CASE-003",
            case_number="00163525",
            subject="ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล",
            intent_type="CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล",
            status="Open",
            citizen_id="9280635310483",
            new_first_name="ใหม่",
            new_last_name="ใหม่",
            verification_documents=[],  # No documents
        )

        result = analyzer.analyze(case)
        assert result.status == ProcessingStatus.SKIPPED
        assert "VALIDATION_FAILED" in result.reason

        # DB unchanged
        record = data_store.get("9280635310483")
        assert record["first_name"] == "ปิติกรณ์"

    def test_cid_not_in_store(self, pipeline):
        """Valid case but CID doesn't exist in store → FAILED."""
        analyzer, _, _ = pipeline

        case = SFCase(
            case_id="CASE-004",
            case_number="00163526",
            subject="ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล",
            intent_type="CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล",
            status="Open",
            citizen_id="UNKNOWN_CID_999",
            new_first_name="X",
            new_last_name="Y",
            verification_documents=[
                VerificationDocument(doc_id="DOC-1", name="id.pdf", size_bytes=100),
            ],
        )

        result = analyzer.analyze(case)
        assert result.status == ProcessingStatus.FAILED
        assert "CID_NOT_FOUND" in result.reason

    def test_phone_change_no_doc_required(self, pipeline):
        """Phone change doesn't require document → auto-approved."""
        analyzer, data_store, _ = pipeline

        case = SFCase(
            case_id="CASE-005",
            case_number="00163527",
            subject="ขอใช้บริการ:CC - ข้อมูลส่วนตัว - หมายเลขโทรศัพท์ในการติดต่อ",
            intent_type="CC - ข้อมูลส่วนตัว - หมายเลขโทรศัพท์ในการติดต่อ",
            status="Open",
            citizen_id="9280635310483",
            new_first_name="099-999-9999",  # Phone stored in Process_Add_Info_1
            verification_documents=[],  # No doc needed
        )

        result = analyzer.analyze(case)
        assert result.status == ProcessingStatus.COMPLETED

        record = data_store.get("9280635310483")
        assert record["phone"] == "099-999-9999"

    def test_email_change_no_doc_required(self, pipeline):
        """Email change doesn't require document → auto-approved."""
        analyzer, data_store, _ = pipeline

        case = SFCase(
            case_id="CASE-006",
            case_number="00163528",
            subject="ขอใช้บริการ:CC - ข้อมูลส่วนตัว - อีเมล",
            intent_type="CC - ข้อมูลส่วนตัว - อีเมล",
            status="Open",
            citizen_id="1234567890123",
            new_first_name="new@company.com",  # Email stored in Process_Add_Info_1
            verification_documents=[],
        )

        result = analyzer.analyze(case)
        assert result.status == ProcessingStatus.COMPLETED

        record = data_store.get("1234567890123")
        assert record["email"] == "new@company.com"

    def test_multiple_cases_isolation(self, pipeline):
        """Multiple cases — one failure doesn't affect others."""
        analyzer, data_store, _ = pipeline

        cases = [
            # Case 1: valid name change
            SFCase(
                case_id="C1", case_number="001",
                subject="s", intent_type="CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล",
                status="Open", citizen_id="9280635310483",
                new_first_name="AAA", new_last_name="BBB",
                verification_documents=[VerificationDocument(doc_id="D1", name="f.pdf", size_bytes=100)],
            ),
            # Case 2: missing intent (will be skipped)
            SFCase(
                case_id="C2", case_number="002",
                subject="", intent_type="",
                status="Open", citizen_id="9280635310483",
            ),
            # Case 3: valid phone change
            SFCase(
                case_id="C3", case_number="003",
                subject="s", intent_type="CC - ข้อมูลส่วนตัว - หมายเลขโทรศัพท์ในการติดต่อ",
                status="Open", citizen_id="1234567890123",
                new_first_name="088-888-8888",
            ),
        ]

        results = [analyzer.analyze(case) for case in cases]

        assert results[0].status == ProcessingStatus.COMPLETED
        assert results[1].status == ProcessingStatus.SKIPPED
        assert results[2].status == ProcessingStatus.COMPLETED

        # Verify both updates applied
        assert data_store.get("9280635310483")["first_name"] == "AAA"
        assert data_store.get("1234567890123")["phone"] == "088-888-8888"
