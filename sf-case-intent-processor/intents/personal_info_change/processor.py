"""PersonalInfoChangeProcessor — handles all Customer Information Update intents."""

import logging
from intent_analyzer.base_processor import IntentProcessor
from sf_case_extractor.models import SFCase
from shared.models import ProcessingResult, ProcessingStatus, ValidationResult
from document_validator.validator import DocumentValidator
from customer_data_store.store import CustomerDataStore
from intents.personal_info_change.field_map import get_intent_config, SUPPORTED_INTENTS

logger = logging.getLogger(__name__)


class PersonalInfoChangeProcessor(IntentProcessor):
    """Processes Customer Information Update cases.

    Flow:
    1. validate() — delegates to DocumentValidator
    2. process() — maps intent to fields, updates CustomerDataStore
    """

    # Class-level constant for registration
    SUPPORTED_INTENTS = SUPPORTED_INTENTS

    def __init__(self, doc_validator: DocumentValidator, data_store: CustomerDataStore):
        self._doc_validator = doc_validator
        self._data_store = data_store

    def validate(self, case: SFCase) -> ValidationResult:
        """Validate that required documents are attached.

        For intents that don't require documents (phone, email, address),
        validation always passes.
        """
        config = get_intent_config(case.intent_name)
        if not config:
            return ValidationResult(ok=False, reason=f"No config for intent: {case.intent_name}")

        # Some intents don't require document verification
        required_doc = config.get("required_doc", "")
        if "ไม่ต้องใช้เอกสาร" in required_doc:
            return ValidationResult(ok=True)

        # For intents requiring documents, delegate to DocumentValidator
        return self._doc_validator.validate(case)

    def process(self, case: SFCase) -> ProcessingResult:
        """Update customer record based on intent type.

        Maps intent → source fields (from SFCase) → target fields (in CustomerDataStore).
        """
        config = get_intent_config(case.intent_name)
        if not config:
            return ProcessingResult(
                case_id=case.case_id,
                status=ProcessingStatus.FAILED,
                reason=f"No config for intent: {case.intent_name}",
            )

        source_fields = config["source_fields"]
        target_fields = config["target_fields"]
        cid = case.cid

        if not cid:
            logger.error(f"Case {case.case_id}: no citizen ID (CID) — cannot update")
            return ProcessingResult(
                case_id=case.case_id,
                status=ProcessingStatus.FAILED,
                reason="NO_CID",
            )

        # Update each target field
        updated_fields = []
        for source_field, target_field in zip(source_fields, target_fields):
            new_value = getattr(case, source_field, None)
            if not new_value:
                logger.warning(f"Case {case.case_id}: source field '{source_field}' is empty — skipping")
                continue

            result = self._data_store.update(cid, target_field, new_value)
            if not result.ok:
                return ProcessingResult(
                    case_id=case.case_id,
                    status=ProcessingStatus.FAILED,
                    reason=f"Update failed for {target_field}: {result.reason}",
                    cid=cid,
                )
            updated_fields.append(target_field)

        if not updated_fields:
            return ProcessingResult(
                case_id=case.case_id,
                status=ProcessingStatus.SKIPPED,
                reason="NO_FIELDS_TO_UPDATE",
                cid=cid,
            )

        logger.info(
            f"Case {case.case_id}: updated {', '.join(updated_fields)} for CID {cid}",
            extra={"case_id": case.case_id, "cid": cid}
        )
        return ProcessingResult(
            case_id=case.case_id,
            status=ProcessingStatus.COMPLETED,
            field_updated=", ".join(updated_fields),
            cid=cid,
        )
