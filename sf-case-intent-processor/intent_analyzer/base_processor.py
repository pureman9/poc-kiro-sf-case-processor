"""IntentProcessor Abstract Base Class — all intent processors must implement this."""

from abc import ABC, abstractmethod
from sf_case_extractor.models import SFCase
from shared.models import ProcessingResult, ValidationResult


class IntentProcessor(ABC):
    """Abstract base class for intent processors.

    Each concrete processor must implement:
    - validate(): check if the case meets requirements (e.g., document attached)
    - process(): execute the business action (e.g., update customer record)
    """

    @abstractmethod
    def validate(self, case: SFCase) -> ValidationResult:
        """Run validation rules for this intent.

        Returns:
            ValidationResult with ok=True if validation passes, ok=False with reason if not.
        """
        ...

    @abstractmethod
    def process(self, case: SFCase) -> ProcessingResult:
        """Execute processing actions after successful validation.

        Returns:
            ProcessingResult with status=COMPLETED on success, FAILED on error.
        """
        ...
