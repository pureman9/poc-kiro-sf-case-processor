"""Unit tests for IntentRegistry."""

import pytest
from intent_analyzer.registry import IntentRegistry
from intent_analyzer.base_processor import IntentProcessor
from sf_case_extractor.models import SFCase
from shared.models import ProcessingResult, ProcessingStatus, ValidationResult
from shared.exceptions import RegistrationError


class MockProcessor(IntentProcessor):
    def validate(self, case): return ValidationResult(ok=True)
    def process(self, case): return ProcessingResult(case_id=case.case_id, status=ProcessingStatus.COMPLETED)


class TestIntentRegistry:

    def test_register_and_get(self):
        reg = IntentRegistry()
        proc = MockProcessor()
        reg.register("test-intent", proc)
        assert reg.get("test-intent") is proc

    def test_get_nonexistent_returns_none(self):
        reg = IntentRegistry()
        assert reg.get("unknown") is None

    def test_duplicate_registration_raises(self):
        reg = IntentRegistry()
        reg.register("intent-a", MockProcessor())
        with pytest.raises(RegistrationError, match="Duplicate"):
            reg.register("intent-a", MockProcessor())

    def test_empty_intent_name_raises(self):
        reg = IntentRegistry()
        with pytest.raises(RegistrationError, match="cannot be empty"):
            reg.register("", MockProcessor())

    def test_whitespace_intent_name_raises(self):
        reg = IntentRegistry()
        with pytest.raises(RegistrationError, match="cannot be empty"):
            reg.register("   ", MockProcessor())

    def test_invalid_processor_raises(self):
        reg = IntentRegistry()
        with pytest.raises(RegistrationError, match="must implement"):
            reg.register("intent-x", "not a processor")  # type: ignore

    def test_registered_intents_property(self):
        reg = IntentRegistry()
        reg.register("a", MockProcessor())
        reg.register("b", MockProcessor())
        assert sorted(reg.registered_intents) == ["a", "b"]
