"""Unit tests for SFCase and VerificationDocument dataclasses."""

import pytest
from sf_case_extractor.models import SFCase, VerificationDocument


class TestVerificationDocument:
    """Tests for VerificationDocument.is_valid() method."""

    def test_status_ok_uppercase(self):
        doc = VerificationDocument(doc_id="DOC-001", status="OK")
        assert doc.is_valid() is True

    def test_status_valid_lowercase(self):
        doc = VerificationDocument(doc_id="DOC-002", status="valid")
        assert doc.is_valid() is True

    def test_status_ok_lowercase(self):
        doc = VerificationDocument(doc_id="DOC-003", status="ok")
        assert doc.is_valid() is True

    def test_status_valid_uppercase(self):
        doc = VerificationDocument(doc_id="DOC-004", status="VALID")
        assert doc.is_valid() is True

    def test_status_ok_with_spaces(self):
        doc = VerificationDocument(doc_id="DOC-005", status="  OK  ")
        assert doc.is_valid() is True

    def test_status_pending_is_invalid(self):
        doc = VerificationDocument(doc_id="DOC-006", status="PENDING")
        assert doc.is_valid() is False

    def test_status_rejected_is_invalid(self):
        doc = VerificationDocument(doc_id="DOC-007", status="REJECTED")
        assert doc.is_valid() is False

    def test_status_empty_raises_error(self):
        with pytest.raises(ValueError, match="status must be a non-empty string"):
            VerificationDocument(doc_id="DOC-008", status="")

    def test_doc_id_empty_raises_error(self):
        with pytest.raises(ValueError, match="doc_id must be a non-empty string"):
            VerificationDocument(doc_id="", status="OK")

    def test_doc_id_whitespace_raises_error(self):
        with pytest.raises(ValueError, match="doc_id must be a non-empty string"):
            VerificationDocument(doc_id="   ", status="OK")


class TestSFCase:
    """Tests for SFCase dataclass validation."""

    def test_valid_case_creation(self):
        case = SFCase(
            case_id="5001000000D8cuI",
            cid="C001234",
            intent_name="ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ",
            status="Open",
            new_value="สมศักดิ์",
        )
        assert case.case_id == "5001000000D8cuI"
        assert case.cid == "C001234"
        assert case.new_value == "สมศักดิ์"
        assert case.verification_documents == []

    def test_case_with_documents(self):
        docs = [
            VerificationDocument(doc_id="DOC-001", status="OK"),
            VerificationDocument(doc_id="DOC-002", status="PENDING"),
        ]
        case = SFCase(
            case_id="CASE-001",
            cid="C002345",
            intent_name="test-intent",
            status="New",
            verification_documents=docs,
        )
        assert len(case.verification_documents) == 2
        assert case.verification_documents[0].is_valid() is True
        assert case.verification_documents[1].is_valid() is False

    def test_case_id_empty_raises_error(self):
        with pytest.raises(ValueError, match="case_id must be a non-empty string"):
            SFCase(case_id="", cid="C001", intent_name="test", status="Open")

    def test_cid_empty_raises_error(self):
        with pytest.raises(ValueError, match="cid must be a non-empty string"):
            SFCase(case_id="CASE-001", cid="", intent_name="test", status="Open")

    def test_new_value_none_is_allowed(self):
        case = SFCase(case_id="CASE-001", cid="C001", intent_name="test", status="Open")
        assert case.new_value is None
