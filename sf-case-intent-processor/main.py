"""SF Case Intent Processor — Pipeline Runner.

Orchestrates: Extract → Analyze → Validate → Update → Mobius Sync → Close SF Case
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from config import load_config
from shared.logger import setup_logger
from shared.exceptions import ExtractionError, StorageInitError
from shared.models import ProcessingStatus
from sf_case_extractor.extractor import SFCaseExtractor
from sf_case_extractor.case_updater import SFCaseUpdater
from intent_analyzer.analyzer import IntentAnalyzer
from intent_analyzer.registry import IntentRegistry
from document_validator.validator import DocumentValidator
from customer_data_store.store import CustomerDataStore
from intents.personal_info_change.processor import PersonalInfoChangeProcessor
from intents.personal_info_change.field_map import SUPPORTED_INTENTS, get_intent_config
from mobius_client.client import MobiusClient
from mobius_client.models import thai_title_to_mobius_code


def build_registry(doc_validator: DocumentValidator, data_store: CustomerDataStore) -> IntentRegistry:
    """Register all known intent processors."""
    registry = IntentRegistry()
    processor = PersonalInfoChangeProcessor(doc_validator, data_store)

    for intent_name in SUPPORTED_INTENTS:
        registry.register(intent_name, processor)

    return registry


def sync_to_mobius(case, mobius: MobiusClient, logger) -> bool:
    """Sync customer name/title change to Mobius after local update.

    Flow:
    1. Search customer by citizen ID → get customerId (CIF)
    2. Update name/title in Mobius using customerId
    """
    citizen_id = case.cid
    if not citizen_id:
        logger.warning(f"Case {case.case_id}: no citizen ID — skipping Mobius sync")
        return False

    # Step 1: Find customer in Mobius
    search_result = mobius.search_customer_by_cid(citizen_id)
    if not search_result.ok:
        logger.error(f"Case {case.case_id}: Mobius search failed — {search_result.message}")
        return False

    customer_id = search_result.customer_id

    # Step 2: Determine what to update based on intent
    config = get_intent_config(case.intent_name)
    if not config:
        logger.warning(f"Case {case.case_id}: no intent config for Mobius sync")
        return False

    target_fields = config.get("target_fields", [])

    # ── Address update ─────────────────────────────────────────────────────────
    if "address" in target_fields:
        # For address, new_first_name contains the full address string from SF
        address_text = case.new_first_name or ""
        if not address_text:
            logger.warning(f"Case {case.case_id}: no address data — skipping Mobius")
            return False

        update_result = mobius.update_customer_address(
            customer_id=customer_id,
            address_number=address_text,  # Full address in one field for now
            address_type="H",  # Home address
            address_format="L",  # Local standard
        )

        if update_result.ok:
            logger.info(f"Case {case.case_id}: Mobius address sync SUCCESS — customerId={customer_id}")
            return True
        else:
            logger.error(f"Case {case.case_id}: Mobius address update failed — {update_result.message}")
            return False

    # ── Phone update ───────────────────────────────────────────────────────────
    if "phone" in target_fields:
        phone_number = case.new_first_name or ""  # Phone stored in Process_Add_Info_1
        if not phone_number:
            logger.warning(f"Case {case.case_id}: no phone data — skipping Mobius")
            return False

        update_result = mobius.update_customer_phone(customer_id, phone_number)
        if update_result.ok:
            logger.info(f"Case {case.case_id}: Mobius phone sync SUCCESS — customerId={customer_id}")
            return True
        else:
            logger.error(f"Case {case.case_id}: Mobius phone update failed — {update_result.message}")
            return False

    # ── Email update ───────────────────────────────────────────────────────────
    if "email" in target_fields:
        email = case.new_first_name or ""  # Email stored in Process_Add_Info_1
        if not email:
            logger.warning(f"Case {case.case_id}: no email data — skipping Mobius")
            return False

        update_result = mobius.update_customer_email(customer_id, email)
        if update_result.ok:
            logger.info(f"Case {case.case_id}: Mobius email sync SUCCESS — customerId={customer_id}")
            return True
        else:
            logger.error(f"Case {case.case_id}: Mobius email update failed — {update_result.message}")
            return False

    # ── Name/Title update ──────────────────────────────────────────────────────
    title_code = None
    thai_first = None
    thai_last = None

    if "title" in target_fields and case.new_title:
        title_code = thai_title_to_mobius_code(case.new_title)
        if not title_code:
            title_code = case.new_title  # Pass as-is if not in map

    if "first_name" in target_fields and case.new_first_name:
        thai_first = case.new_first_name

    if "last_name" in target_fields and case.new_last_name:
        thai_last = case.new_last_name

    # Step 3: Call Mobius update
    update_result = mobius.update_customer_name(
        customer_id=customer_id,
        title_code=title_code,
        thai_first_name=thai_first,
        thai_last_name=thai_last,
    )

    if update_result.ok:
        logger.info(f"Case {case.case_id}: Mobius sync SUCCESS — customerId={customer_id}")
        return True
    else:
        logger.error(f"Case {case.case_id}: Mobius update failed — {update_result.message}")
        return False


def run():
    """Main pipeline execution."""
    config = load_config()
    logger = setup_logger(level=config.log_level)

    logger.info("Pipeline starting")
    logger.info(f"Registered intents: {len(SUPPORTED_INTENTS)}")

    # Initialize components
    try:
        extractor = SFCaseExtractor(config)
        doc_validator = DocumentValidator()
        data_store = CustomerDataStore(config.customer_data_path)
        registry = build_registry(doc_validator, data_store)
        analyzer = IntentAnalyzer(registry)
        mobius = MobiusClient()
    except StorageInitError as e:
        logger.error(f"Pipeline aborted: storage init failed — {e}")
        return

    # Extract cases from Salesforce
    try:
        cases = extractor.extract(include_closed=False)
    except ExtractionError as e:
        logger.error(f"Pipeline aborted: extraction failed — {e}")
        return

    logger.info(f"Extracted {len(cases)} cases for processing")

    if not cases:
        logger.info("No cases to process — pipeline complete")
        return

    # Get SF connection for case updates
    sf_updater = SFCaseUpdater(extractor._sf)

    # Process each case (per-case error isolation)
    results = []
    for case in cases:
        # Step 1: Analyze (validate + update local store)
        result = analyzer.analyze(case)
        results.append(result)

        logger.info(
            f"Case #{case.case_number}: {result.status.value}"
            f" — {result.reason or result.field_updated or ''}",
            extra={"case_id": case.case_id, "cid": case.cid}
        )

        # Step 2: If completed, sync to Mobius
        if result.status == ProcessingStatus.COMPLETED:
            intent_config = get_intent_config(case.intent_name)
            mobius_fields = {"first_name", "last_name", "title", "address", "phone", "email"}
            if intent_config and any(f in mobius_fields for f in intent_config.get("target_fields", [])):
                mobius_ok = sync_to_mobius(case, mobius, logger)
                result.mobius_synced = mobius_ok
            else:
                logger.info(f"Case #{case.case_number}: skipping Mobius (no matching target fields)")
                result.mobius_synced = False

            # Step 3: Close SF case
            sf_closed = sf_updater.close_case(case.case_id, sub_status="Done")
            if sf_closed:
                logger.info(f"Case #{case.case_number}: SF case closed (Done)")
            else:
                logger.warning(f"Case #{case.case_number}: failed to close SF case")

    # Summary
    completed = sum(1 for r in results if r.status == ProcessingStatus.COMPLETED)
    skipped = sum(1 for r in results if r.status == ProcessingStatus.SKIPPED)
    failed = sum(1 for r in results if r.status == ProcessingStatus.FAILED)
    mobius_synced = sum(1 for r in results if r.mobius_synced)

    logger.info(f"Pipeline complete — {completed} completed, {skipped} skipped, {failed} failed, {mobius_synced} synced to Mobius")
    print(f"\n{'='*60}")
    print(f"  Pipeline Summary")
    print(f"  Total:        {len(results)} cases")
    print(f"  Completed:    {completed}")
    print(f"  Skipped:      {skipped}")
    print(f"  Failed:       {failed}")
    print(f"  Mobius Synced: {mobius_synced}")
    print(f"  SF Closed:    {completed}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run()
