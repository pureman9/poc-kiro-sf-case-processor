"""Unit tests for IntentAnalyzer."""

import pytest
from unittest.mock import MagicMock
from intent_analyzer.analyzer import IntentAnalyzer
from intent_analyzer.registry import IntentRegistry
from intent_analyzer.base_processor import IntentProcessor
from sf_case_extractor.models import SFCase
from shared.models import ProcessingResult, ProcessingStatus, ValidationResult


def make_case(intent_type="CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล", case_id="CASE-001"):
    return SFCase(
        case_id=case_id,
        case_number="001",
        subject=f"ขอใช้บริการ:{intent_type}",
        intent_type=intent_type,
        status="Open",
    )


class MockProcessor(IntentProcessor):
    def __init__(self, validate_ok=True, process_result=None):
        self._validate_ok = validate_ok
        self._process_result = process_result

    def validate(self, case):
        if self._validate_ok:
            return ValidationResult(ok=True)
        return ValidationResult(ok=False, reason="DOC_MISSING")

    def process(self, case):
        if self._process_result:
            return self._process_result
        return ProcessingResult(case_id=case.case_id, status=ProcessingStatus.COMPLETED, field_updated="first_name")


class TestIntentAnalyzer:

    def test_missing_intent_returns_skipped(self):
        reg = IntentRegistry()
        analyzer = IntentAnalyzer(reg)
        case = SFCase(case_id="C1", case_number="001", subject="", intent_type="", status="Open")
        result = analyzer.analyze(case)
        assert result.status == ProcessingStatus.SKIPPED
        assert result.reason == "MISSING_INTENT"

    def test_unrecognized_intent_returns_skipped(self):
        reg = IntentRegistry()
        analyzer = IntentAnalyzer(reg)
        case = make_case(intent_type="UNKNOWN_INTENT")
        result = analyzer.analyze(case)
        assert result.status == ProcessingStatus.SKIPPED
        assert result.reason == "UNRECOGNIZED_INTENT"

    def test_validation_failure_returns_skipped(self):
        reg = IntentRegistry()
        proc = MockProcessor(validate_ok=False)
        intent = "CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล"
        reg.register(intent, proc)
        analyzer = IntentAnalyzer(reg)
        case = make_case(intent_type=intent)
        result = analyzer.analyze(case)
        assert result.status == ProcessingStatus.SKIPPED
        assert "VALIDATION_FAILED" in result.reason

    def test_successful_processing(self):
        reg = IntentRegistry()
        proc = MockProcessor(validate_ok=True)
        intent = "CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล"
        reg.register(intent, proc)
        analyzer = IntentAnalyzer(reg)
        case = make_case(intent_type=intent)
        result = analyzer.analyze(case)
        assert result.status == ProcessingStatus.COMPLETED
        assert result.field_updated == "first_name"

    def test_processor_exception_returns_failed(self):
        reg = IntentRegistry()
        proc = MagicMock(spec=IntentProcessor)
        proc.validate.return_value = ValidationResult(ok=True)
        proc.process.side_effect = RuntimeError("DB connection lost")
        intent = "test-intent"
        reg.register(intent, proc)
        analyzer = IntentAnalyzer(reg)
        case = make_case(intent_type=intent)
        result = analyzer.analyze(case)
        assert result.status == ProcessingStatus.FAILED
        assert "DB connection lost" in result.reason

    def test_calls_validate_before_process(self):
        reg = IntentRegistry()
        proc = MagicMock(spec=IntentProcessor)
        proc.validate.return_value = ValidationResult(ok=True)
        proc.process.return_value = ProcessingResult(case_id="C1", status=ProcessingStatus.COMPLETED)
        intent = "test-intent"
        reg.register(intent, proc)
        analyzer = IntentAnalyzer(reg)
        case = make_case(intent_type=intent)
        analyzer.analyze(case)
        proc.validate.assert_called_once_with(case)
        proc.process.assert_called_once_with(case)
