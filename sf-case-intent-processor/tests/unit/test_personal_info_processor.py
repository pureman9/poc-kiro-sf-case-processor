"""Unit tests for PersonalInfoChangeProcessor."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from intents.personal_info_change.processor import PersonalInfoChangeProcessor
from document_validator.validator import DocumentValidator
from customer_data_store.store import CustomerDataStore
from sf_case_extractor.models import SFCase, VerificationDocument
from shared.models import ProcessingStatus


SAMPLE_DATA = {
    "9280635310483": {
        "cid": "9280635310483",
        "title": "นาย",
        "first_name": "ปิติกรณ์",
        "last_name": "ใจดี",
        "phone": "081-234-5678",
        "email": "test@email.com",
        "address": "123 ถนนสุขุมวิท",
    },
}


@pytest.fixture
def data_file(tmp_path: Path) -> Path:
    f = tmp_path / "customer_data.json"
    f.write_text(json.dumps(SAMPLE_DATA, ensure_ascii=False, indent=2), encoding="utf-8")
    return f


@pytest.fixture
def processor(data_file):
    doc_validator = DocumentValidator()
    data_store = CustomerDataStore(str(data_file))
    return PersonalInfoChangeProcessor(doc_validator, data_store)


def make_case(intent_type, new_first=None, new_last=None, new_title=None, docs=None):
    return SFCase(
        case_id="CASE-TEST",
        case_number="99999",
        subject=f"ขอใช้บริการ:{intent_type}",
        intent_type=intent_type,
        status="Open",
        citizen_id="9280635310483",
        new_first_name=new_first,
        new_last_name=new_last,
        new_title=new_title,
        verification_documents=docs or [],
    )


class TestValidate:

    def test_validate_with_doc_passes(self, processor):
        case = make_case(
            "CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล",
            docs=[VerificationDocument(doc_id="D1", name="id.pdf", size_bytes=50000)],
        )
        result = processor.validate(case)
        assert result.ok is True

    def test_validate_no_doc_fails(self, processor):
        case = make_case("CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล", docs=[])
        result = processor.validate(case)
        assert result.ok is False
        assert result.reason == "NO_DOCUMENT"

    def test_validate_phone_no_doc_required(self, processor):
        case = make_case("CC - ข้อมูลส่วนตัว - หมายเลขโทรศัพท์ในการติดต่อ", docs=[])
        result = processor.validate(case)
        assert result.ok is True  # No doc required for phone

    def test_validate_email_no_doc_required(self, processor):
        case = make_case("CC - ข้อมูลส่วนตัว - อีเมล", docs=[])
        result = processor.validate(case)
        assert result.ok is True


class TestProcess:

    def test_process_name_change(self, processor, data_file):
        case = make_case(
            "CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล",
            new_first="ดารุณี", new_last="อะฟาฟ",
        )
        result = processor.process(case)
        assert result.status == ProcessingStatus.COMPLETED
        assert "first_name" in result.field_updated
        assert "last_name" in result.field_updated
        # Verify data persisted
        store = CustomerDataStore(str(data_file))
        record = store.get("9280635310483")
        assert record["first_name"] == "ดารุณี"
        assert record["last_name"] == "อะฟาฟ"
        assert record["title"] == "นาย"  # unchanged

    def test_process_first_name_only(self, processor, data_file):
        case = make_case("CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ", new_first="สมศักดิ์")
        result = processor.process(case)
        assert result.status == ProcessingStatus.COMPLETED
        store = CustomerDataStore(str(data_file))
        assert store.get("9280635310483")["first_name"] == "สมศักดิ์"
        assert store.get("9280635310483")["last_name"] == "ใจดี"  # unchanged

    def test_process_title_change(self, processor, data_file):
        case = make_case("CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงคำนำหน้า", new_title="นาง")
        result = processor.process(case)
        assert result.status == ProcessingStatus.COMPLETED
        store = CustomerDataStore(str(data_file))
        assert store.get("9280635310483")["title"] == "นาง"

    def test_process_no_cid_fails(self, processor):
        case = SFCase(
            case_id="C1", case_number="001",
            subject="test", intent_type="CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ",
            status="Open", citizen_id=None, new_first_name="X",
        )
        result = processor.process(case)
        assert result.status == ProcessingStatus.FAILED
        assert result.reason == "NO_CID"

    def test_process_cid_not_in_store(self, processor):
        case = SFCase(
            case_id="C1", case_number="001",
            subject="test", intent_type="CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ",
            status="Open", citizen_id="UNKNOWN_CID", new_first_name="X",
        )
        result = processor.process(case)
        assert result.status == ProcessingStatus.FAILED
        assert "CID_NOT_FOUND" in result.reason

    def test_process_empty_source_field_skips(self, processor):
        case = make_case("CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ", new_first=None)
        result = processor.process(case)
        assert result.status == ProcessingStatus.SKIPPED
        assert result.reason == "NO_FIELDS_TO_UPDATE"
