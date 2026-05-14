"""IntentRegistry — maps intent names to processors. Enforces registration rules."""

import logging
from intent_analyzer.base_processor import IntentProcessor
from shared.exceptions import RegistrationError

logger = logging.getLogger(__name__)


class IntentRegistry:
    """Registry of intent name → processor mappings.

    Rules:
    - Each intent name maps to exactly one processor
    - Duplicate registrations are rejected
    - Processors must implement IntentProcessor ABC (validate + process)
    """

    def __init__(self):
        self._processors: dict[str, IntentProcessor] = {}

    def register(self, intent_name: str, processor: IntentProcessor) -> None:
        """Register a processor for a given intent name.

        Args:
            intent_name: Exact intent type string (e.g., "CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล")
            processor: An instance implementing IntentProcessor ABC.

        Raises:
            RegistrationError: If intent_name is already registered or processor is invalid.
        """
        if not intent_name or not intent_name.strip():
            raise RegistrationError("Intent name cannot be empty")

        if not isinstance(processor, IntentProcessor):
            raise RegistrationError(
                f"Processor must implement IntentProcessor ABC (got {type(processor).__name__})"
            )

        if intent_name in self._processors:
            raise RegistrationError(
                f"Duplicate intent registration: '{intent_name}' already has a processor"
            )

        self._processors[intent_name] = processor
        logger.debug(f"Registered processor for intent: {intent_name}")

    def get(self, intent_name: str) -> IntentProcessor | None:
        """Look up a processor by exact intent name.

        Returns:
            The registered IntentProcessor, or None if not found.
        """
        return self._processors.get(intent_name)

    @property
    def registered_intents(self) -> list[str]:
        """Return list of all registered intent names."""
        return list(self._processors.keys())
