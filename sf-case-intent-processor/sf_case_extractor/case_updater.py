"""Salesforce Case Updater — close cases after successful processing."""

import logging
from simple_salesforce import Salesforce

logger = logging.getLogger(__name__)


class SFCaseUpdater:
    """Updates Salesforce case status after processing."""

    def __init__(self, sf: Salesforce):
        self._sf = sf

    def close_case(self, case_id: str, sub_status: str = "Done") -> bool:
        """Update case Status to 'Closed' and Sub_Status__c to the given value.

        Args:
            case_id: Salesforce Case Id.
            sub_status: Sub-status value (default: "Done").

        Returns:
            True on success, False on failure.
        """
        try:
            self._sf.Case.update(case_id, {
                "Status": "Closed",
                "Sub_Status__c": sub_status,
            })
            logger.info(f"SF Case {case_id}: closed with sub-status '{sub_status}'")
            return True
        except Exception as e:
            logger.error(f"SF Case {case_id}: failed to close — {e}")
            return False
