"""IntentAnalyzer — routes cases to the correct processor via IntentRegistry."""

import logging
from sf_case_extractor.models import SFCase
from shared.models import ProcessingResult, ProcessingStatus
from intent_analyzer.registry import IntentRegistry

logger = logging.getLogger(__name__)


class IntentAnalyzer:
    """Analyzes each case's intent and routes to the appropriate processor.

    Per-case error isolation: one case failure does not halt the pipeline.
    """

    def __init__(self, registry: IntentRegistry):
        self._registry = registry

    def analyze(self, case: SFCase) -> ProcessingResult:
        """Route a case to its registered processor and execute.

        Flow:
        1. Extract intent_name from case
        2. Validate non-empty
        3. Look up processor in registry
        4. Call processor.validate() → if fails, return SKIPPED
        5. Call processor.process() → return result

        Args:
            case: The SFCase to process.

        Returns:
            ProcessingResult with appropriate status.
        """
        try:
            intent_name = case.intent_name

            # Check for missing/empty intent
            if not intent_name or not intent_name.strip():
                logger.warning(
                    f"Case {case.case_id}: missing intent name",
                    extra={"case_id": case.case_id}
                )
                return ProcessingResult(
                    case_id=case.case_id,
                    status=ProcessingStatus.SKIPPED,
                    reason="MISSING_INTENT",
                )

            # Look up processor
            processor = self._registry.get(intent_name)
            if processor is None:
                logger.warning(
                    f"Case {case.case_id}: unrecognized intent '{intent_name}'",
                    extra={"case_id": case.case_id, "intent_name": intent_name}
                )
                return ProcessingResult(
                    case_id=case.case_id,
                    status=ProcessingStatus.SKIPPED,
                    reason="UNRECOGNIZED_INTENT",
                )

            # Validate
            validation = processor.validate(case)
            if not validation.ok:
                logger.warning(
                    f"Case {case.case_id}: validation failed — {validation.reason}",
                    extra={"case_id": case.case_id, "intent_name": intent_name}
                )
                return ProcessingResult(
                    case_id=case.case_id,
                    status=ProcessingStatus.SKIPPED,
                    reason=f"VALIDATION_FAILED: {validation.reason}",
                )

            # Process
            result = processor.process(case)
            return result

        except Exception as e:
            logger.error(
                f"Case {case.case_id}: unexpected error — {e}",
                extra={"case_id": case.case_id}
            )
            return ProcessingResult(
                case_id=case.case_id,
                status=ProcessingStatus.FAILED,
                reason=str(e),
            )
