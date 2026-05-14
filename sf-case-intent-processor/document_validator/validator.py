"""DocumentValidator — verifies that at least one valid document is attached to a case."""

import logging
from sf_case_extractor.models import SFCase
from shared.models import ValidationResult

logger = logging.getLogger(__name__)


class DocumentValidator:
    """Validates that a case has at least one acceptable verification document.

    A document is considered valid if it exists (size > 0).
    At-least-one semantics: if multiple documents exist, case is valid if ANY one passes.
    """

    def validate(self, case: SFCase) -> ValidationResult:
        """Check that at least one valid document is attached.

        Args:
            case: The SFCase to validate.

        Returns:
            ValidationResult with ok=True if at least one valid doc found.
        """
        docs = case.verification_documents

        # No documents attached
        if not docs:
            logger.warning(
                f"Case {case.case_id}: no verification document found",
                extra={"case_id": case.case_id}
            )
            return ValidationResult(ok=False, reason="NO_DOCUMENT")

        # Check if at least one is valid
        for doc in docs:
            if doc.is_valid():
                return ValidationResult(ok=True, doc_id=doc.doc_id)

        # All documents invalid
        first_invalid = docs[0]
        logger.warning(
            f"Case {case.case_id}: all documents invalid — first: {first_invalid.doc_id} (size={first_invalid.size_bytes})",
            extra={"case_id": case.case_id, "doc_id": first_invalid.doc_id}
        )
        return ValidationResult(
            ok=False,
            reason="INVALID_DOCUMENT",
            doc_id=first_invalid.doc_id,
        )
