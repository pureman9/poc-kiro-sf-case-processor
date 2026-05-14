"""SFCaseExtractor — queries Salesforce sandbox for Customer Information Update cases."""

import time
import logging
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed, SalesforceExpiredSession

from config import AppConfig
from shared.exceptions import ExtractionError
from sf_case_extractor.models import SFCase, VerificationDocument
from sf_case_extractor.soql_builder import build_ciu_query, build_case_attachments_query, build_case_content_docs_query

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
QUERY_TIMEOUT_SECONDS = 30


class SFCaseExtractor:
    """Extracts Customer Information Update cases from Salesforce sandbox."""

    def __init__(self, config: AppConfig):
        self.config = config
        self._sf: Salesforce | None = None

    def _connect(self) -> Salesforce:
        """Establish or return existing Salesforce connection."""
        if self._sf is None:
            self._sf = Salesforce(
                username=self.config.sf_username,
                password=self.config.sf_password,
                security_token=self.config.sf_security_token,
                domain=self.config.sf_domain,
            )
            logger.info("Connected to Salesforce", extra={"instance": self._sf.sf_instance})
        return self._sf

    def _reconnect(self) -> Salesforce:
        """Force reconnection (e.g., after expired session)."""
        self._sf = None
        return self._connect()

    def extract(self, include_closed: bool = False, limit: int | None = None) -> list[SFCase]:
        """Extract all Customer Information Update cases from Salesforce.

        Args:
            include_closed: If True, also fetch closed cases (for testing/analysis).
            limit: Max number of cases to fetch.

        Returns:
            List of SFCase objects.

        Raises:
            ExtractionError: After all retries exhausted or auth failure.
        """
        soql = build_ciu_query(include_closed=include_closed, limit=limit)
        logger.info("Starting extraction", extra={"query_preview": soql[:80]})

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                sf = self._connect()
                result = sf.query(soql)
                cases = self._parse_cases(result, sf)
                logger.info(f"Extraction complete: {len(cases)} cases found")
                return cases

            except SalesforceAuthenticationFailed as e:
                logger.error(f"Authentication failed — not retrying: {e}")
                raise ExtractionError(f"Salesforce auth failed: {e}")

            except SalesforceExpiredSession:
                logger.warning("Session expired — reconnecting")
                self._reconnect()
                # Don't count this as a retry attempt
                continue

            except Exception as e:
                if attempt == MAX_RETRIES:
                    logger.error(f"Extraction failed after {MAX_RETRIES} attempts: {e}")
                    raise ExtractionError(f"Failed after {MAX_RETRIES} retries: {e}")
                logger.warning(f"Attempt {attempt} failed, retrying in {RETRY_DELAY_SECONDS}s: {e}")
                time.sleep(RETRY_DELAY_SECONDS)

        return []  # Should not reach here

    def _parse_cases(self, result: dict, sf: Salesforce) -> list[SFCase]:
        """Parse Salesforce query result into SFCase objects."""
        cases = []
        for record in result.get('records', []):
            try:
                case_id = record['Id']

                # Fetch attachments for this case
                docs = self._fetch_documents(case_id, sf)

                case = SFCase(
                    case_id=case_id,
                    case_number=record.get('CaseNumber', ''),
                    subject=record.get('Subject', ''),
                    intent_type=record.get('Type__c', ''),
                    status=record.get('Status', ''),
                    sub_status=record.get('Sub_Status__c'),
                    category=record.get('Category__c'),
                    customer_name=record.get('Customer_Name__c'),
                    citizen_id=record.get('Process_Add_Info_9__c'),
                    new_first_name=record.get('Process_Add_Info_1__c'),
                    new_last_name=record.get('Process_Add_Info_2__c'),
                    new_title=record.get('Process_Add_Info_3__c'),
                    old_name=record.get('Process_Add_Info_4__c'),
                    contact_id=record.get('ContactId'),
                    account_id=record.get('AccountId'),
                    verification_documents=docs,
                )
                cases.append(case)
            except Exception as e:
                logger.warning(f"Failed to parse case record: {e}", extra={"record_id": record.get('Id')})
                continue

        return cases

    def _fetch_documents(self, case_id: str, sf: Salesforce) -> list[VerificationDocument]:
        """Fetch attachments and content documents for a case."""
        docs = []

        # Try Attachments
        try:
            att_query = build_case_attachments_query(case_id)
            att_result = sf.query(att_query)
            for att in att_result.get('records', []):
                docs.append(VerificationDocument(
                    doc_id=att['Id'],
                    name=att.get('Name', 'unknown'),
                    content_type=att.get('ContentType'),
                    size_bytes=att.get('BodyLength', 0),
                ))
        except Exception as e:
            logger.debug(f"Could not fetch attachments for {case_id}: {e}")

        # Try ContentDocumentLinks
        try:
            cdl_query = build_case_content_docs_query(case_id)
            cdl_result = sf.query(cdl_query)
            for cdl in cdl_result.get('records', []):
                doc_info = cdl.get('ContentDocument', {})
                docs.append(VerificationDocument(
                    doc_id=cdl.get('ContentDocumentId', ''),
                    name=doc_info.get('Title', 'unknown'),
                    content_type=doc_info.get('FileType'),
                    size_bytes=doc_info.get('ContentSize', 0),
                ))
        except Exception as e:
            logger.debug(f"Could not fetch content docs for {case_id}: {e}")

        return docs
