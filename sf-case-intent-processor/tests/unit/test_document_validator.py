"""Unit tests for DocumentValidator."""

import pytest
from document_validator.validator import DocumentValidator
from sf_case_extractor.models import SFCase, VerificationDocument


def make_case(docs=None):
    return SFCase(
        case_id="CASE-001",
        case_number="001",
        subject="test",
        intent_type="test",
        status="Open",
        verification_documents=docs or [],
    )


class TestDocumentValidator:

    def setup_method(self):
        self.validator = DocumentValidator()

    def test_no_documents_returns_false(self):
        case = make_case(docs=[])
        result = self.validator.validate(case)
        assert result.ok is False
        assert result.reason == "NO_DOCUMENT"

    def test_one_valid_document_returns_true(self):
        case = make_case(docs=[
            VerificationDocument(doc_id="DOC-1", name="ID.pdf", size_bytes=50000),
        ])
        result = self.validator.validate(case)
        assert result.ok is True
        assert result.doc_id == "DOC-1"

    def test_one_invalid_document_zero_size(self):
        case = make_case(docs=[
            VerificationDocument(doc_id="DOC-1", name="empty.pdf", size_bytes=0),
        ])
        result = self.validator.validate(case)
        assert result.ok is False
        assert result.reason == "INVALID_DOCUMENT"
        assert result.doc_id == "DOC-1"

    def test_multiple_docs_one_valid(self):
        case = make_case(docs=[
            VerificationDocument(doc_id="DOC-1", name="empty.pdf", size_bytes=0),
            VerificationDocument(doc_id="DOC-2", name="valid.pdf", size_bytes=120000),
        ])
        result = self.validator.validate(case)
        assert result.ok is True
        assert result.doc_id == "DOC-2"

    def test_multiple_docs_all_invalid(self):
        case = make_case(docs=[
            VerificationDocument(doc_id="DOC-1", name="a.pdf", size_bytes=0),
            VerificationDocument(doc_id="DOC-2", name="b.pdf", size_bytes=0),
        ])
        result = self.validator.validate(case)
        assert result.ok is False
        assert result.reason == "INVALID_DOCUMENT"

    def test_multiple_docs_all_valid(self):
        case = make_case(docs=[
            VerificationDocument(doc_id="DOC-1", name="a.pdf", size_bytes=100),
            VerificationDocument(doc_id="DOC-2", name="b.pdf", size_bytes=200),
        ])
        result = self.validator.validate(case)
        assert result.ok is True
        # Returns first valid
        assert result.doc_id == "DOC-1"

    def test_large_document_is_valid(self):
        case = make_case(docs=[
            VerificationDocument(doc_id="DOC-BIG", name="scan.jpg", content_type="image/jpeg", size_bytes=5_000_000),
        ])
        result = self.validator.validate(case)
        assert result.ok is True
