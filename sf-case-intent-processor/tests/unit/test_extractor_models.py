"""Unit tests for SFCase and VerificationDocument dataclasses (updated for real schema)."""

import pytest
from sf_case_extractor.models import SFCase, VerificationDocument


class TestVerificationDocument:
    """Tests for VerificationDocument.is_valid() method — now based on size > 0."""

    def test_valid_document_nonzero_size(self):
        doc = VerificationDocument(doc_id="DOC-001", name="id_card.pdf", size_bytes=50000)
        assert doc.is_valid() is True

    def test_invalid_document_zero_size(self):
        doc = VerificationDocument(doc_id="DOC-002", name="empty.pdf", size_bytes=0)
        assert doc.is_valid() is False

    def test_large_document_is_valid(self):
        doc = VerificationDocument(doc_id="DOC-003", name="scan.jpg", size_bytes=5_000_000)
        assert doc.is_valid() is True

    def test_doc_id_empty_raises_error(self):
        with pytest.raises(ValueError, match="doc_id must be a non-empty string"):
            VerificationDocument(doc_id="", name="test.pdf", size_bytes=100)

    def test_doc_id_whitespace_raises_error(self):
        with pytest.raises(ValueError, match="doc_id must be a non-empty string"):
            VerificationDocument(doc_id="   ", name="test.pdf", size_bytes=100)

    def test_name_empty_raises_error(self):
        with pytest.raises(ValueError, match="name must be a non-empty string"):
            VerificationDocument(doc_id="DOC-1", name="", size_bytes=100)

    def test_content_type_optional(self):
        doc = VerificationDocument(doc_id="DOC-1", name="file.pdf", content_type="application/pdf", size_bytes=100)
        assert doc.content_type == "application/pdf"

    def test_content_type_none_default(self):
        doc = VerificationDocument(doc_id="DOC-1", name="file.pdf", size_bytes=100)
        assert doc.content_type is None


class TestSFCase:
    """Tests for SFCase dataclass validation (real schema)."""

    def test_valid_case_creation(self):
        case = SFCase(
            case_id="5001y000003oLngAAE",
            case_number="00001659",
            subject="ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล",
            intent_type="CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล",
            status="Open",
            citizen_id="9280635310483",
            new_first_name="ดารุณี",
            new_last_name="อะฟาฟ",
        )
        assert case.case_id == "5001y000003oLngAAE"
        assert case.case_number == "00001659"
        assert case.intent_name == "CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล"
        assert case.cid == "9280635310483"
        assert case.new_first_name == "ดารุณี"

    def test_case_with_documents(self):
        docs = [
            VerificationDocument(doc_id="DOC-001", name="id.pdf", size_bytes=50000),
            VerificationDocument(doc_id="DOC-002", name="empty.pdf", size_bytes=0),
        ]
        case = SFCase(
            case_id="CASE-001", case_number="001",
            subject="test", intent_type="test-type", status="New",
            verification_documents=docs,
        )
        assert len(case.verification_documents) == 2
        assert case.verification_documents[0].is_valid() is True
        assert case.verification_documents[1].is_valid() is False

    def test_case_id_empty_raises_error(self):
        with pytest.raises(ValueError, match="case_id must be a non-empty string"):
            SFCase(case_id="", case_number="001", subject="s", intent_type="t", status="Open")

    def test_case_number_empty_raises_error(self):
        with pytest.raises(ValueError, match="case_number must be a non-empty string"):
            SFCase(case_id="ID1", case_number="", subject="s", intent_type="t", status="Open")

    def test_intent_name_property(self):
        case = SFCase(case_id="ID1", case_number="001", subject="s", intent_type="MY_TYPE", status="Open")
        assert case.intent_name == "MY_TYPE"

    def test_cid_property_from_citizen_id(self):
        case = SFCase(case_id="ID1", case_number="001", subject="s", intent_type="t", status="Open", citizen_id="1234567890123")
        assert case.cid == "1234567890123"

    def test_cid_property_empty_when_no_citizen_id(self):
        case = SFCase(case_id="ID1", case_number="001", subject="s", intent_type="t", status="Open")
        assert case.cid == ""

    def test_new_value_fields_optional(self):
        case = SFCase(case_id="ID1", case_number="001", subject="s", intent_type="t", status="Open")
        assert case.new_first_name is None
        assert case.new_last_name is None
        assert case.new_title is None
