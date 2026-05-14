"""SF Case Intent Processor — Pipeline Runner.

Orchestrates: Extract → Analyze → Validate → Update
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from config import load_config
from shared.logger import setup_logger
from shared.exceptions import ExtractionError, StorageInitError
from sf_case_extractor.extractor import SFCaseExtractor
from intent_analyzer.analyzer import IntentAnalyzer
from intent_analyzer.registry import IntentRegistry
from document_validator.validator import DocumentValidator
from customer_data_store.store import CustomerDataStore
from intents.personal_info_change.processor import PersonalInfoChangeProcessor
from intents.personal_info_change.field_map import SUPPORTED_INTENTS


def build_registry(doc_validator: DocumentValidator, data_store: CustomerDataStore) -> IntentRegistry:
    """Register all known intent processors."""
    registry = IntentRegistry()
    processor = PersonalInfoChangeProcessor(doc_validator, data_store)

    for intent_name in SUPPORTED_INTENTS:
        registry.register(intent_name, processor)

    return registry


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

    # Process each case (per-case error isolation)
    results = []
    for case in cases:
        result = analyzer.analyze(case)
        results.append(result)
        logger.info(
            f"Case #{case.case_number}: {result.status.value}"
            f" — {result.reason or result.field_updated or ''}",
            extra={"case_id": case.case_id, "cid": case.cid}
        )

    # Summary
    completed = sum(1 for r in results if r.status.value == "COMPLETED")
    skipped = sum(1 for r in results if r.status.value == "SKIPPED")
    failed = sum(1 for r in results if r.status.value == "FAILED")

    logger.info(f"Pipeline complete — {completed} completed, {skipped} skipped, {failed} failed")
    print(f"\n{'='*50}")
    print(f"  Pipeline Summary")
    print(f"  Total:     {len(results)} cases")
    print(f"  Completed: {completed}")
    print(f"  Skipped:   {skipped}")
    print(f"  Failed:    {failed}")
    print(f"{'='*50}")


if __name__ == "__main__":
    run()
