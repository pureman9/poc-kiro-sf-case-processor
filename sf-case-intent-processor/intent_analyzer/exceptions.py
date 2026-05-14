"""Exceptions for the Intent Analyzer module."""


class MissingIntentError(Exception):
    """Raised when a case has no intent name (empty or whitespace)."""
    def __init__(self, case_id: str):
        self.case_id = case_id
        super().__init__(f"Case {case_id} has no intent name")


class UnrecognizedIntentError(Exception):
    """Raised when a case's intent name doesn't match any registered processor."""
    def __init__(self, case_id: str, intent_name: str):
        self.case_id = case_id
        self.intent_name = intent_name
        super().__init__(f"Case {case_id}: unrecognized intent '{intent_name}'")
