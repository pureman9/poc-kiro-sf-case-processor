"""Unit tests for SFCaseExtractor — mocked Salesforce connection."""

import pytest
from unittest.mock import MagicMock, patch
from simple_salesforce import SalesforceAuthenticationFailed

from sf_case_extractor.extractor import SFCaseExtractor, MAX_RETRIES
from sf_case_extractor.models import SFCase
from shared.exceptions import ExtractionError
from config import AppConfig


@pytest.fixture
def config():
    return AppConfig(
        sf_username="test@example.com",
        sf_password="password",
        sf_security_token="token",
        sf_domain="test",
        customer_data_path="./data/customer_data.json",
        log_level="INFO",
        mobius_api_url=None,
        mobius_api_key=None,
        mobius_timeout=30,
        jira_base_url=None,
        jira_api_token=None,
        jira_project_key=None,
        jira_test_plan_key=None,
    )


@pytest.fixture
def mock_sf():
    """Create a mock Salesforce client."""
    return MagicMock()


@pytest.fixture
def extractor(config, mock_sf):
    """Create extractor with mocked SF connection."""
    ext = SFCaseExtractor(config)
    ext._sf = mock_sf
    return ext


class TestExtractSuccess:
    """Tests for successful extraction scenarios."""

    def test_extract_returns_cases(self, extractor, mock_sf):
        mock_sf.query.return_value = {
            'totalSize': 1,
            'records': [{
                'Id': '5001y000003oLngAAE',
                'CaseNumber': '00001659',
                'Subject': 'ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล',
                'Type__c': 'CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล',
                'Status': 'Open',
                'Sub_Status__c': 'Pending Validation',
                'Category__c': 'การจัดการข้อมูลส่วนบุคคล',
                'Customer_Name__c': 'ปิติกรณ์ ใจดี',
                'Process_Add_Info_1__c': 'ดารุณี',
                'Process_Add_Info_2__c': 'อะฟาฟ',
                'Process_Add_Info_3__c': 'อา',
                'Process_Add_Info_4__c': 'ถนอม',
                'Process_Add_Info_9__c': '9280635310483',
                'ContactId': None,
                'AccountId': '0011y00000ROGNgAAP',
            }],
        }

        cases = extractor.extract()

        assert len(cases) == 1
        assert cases[0].case_number == '00001659'
        assert cases[0].intent_type == 'CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล'
        assert cases[0].customer_name == 'ปิติกรณ์ ใจดี'
        assert cases[0].new_first_name == 'ดารุณี'
        assert cases[0].new_last_name == 'อะฟาฟ'
        assert cases[0].cid == '9280635310483'

    def test_extract_empty_result(self, extractor, mock_sf):
        mock_sf.query.return_value = {'totalSize': 0, 'records': []}

        cases = extractor.extract()

        assert cases == []
        assert mock_sf.query.call_count == 1

    def test_extract_multiple_cases(self, extractor, mock_sf):
        mock_sf.query.return_value = {
            'totalSize': 2,
            'records': [
                {'Id': 'ID1', 'CaseNumber': '001', 'Subject': 'S1', 'Type__c': 'T1',
                 'Status': 'Open', 'Sub_Status__c': None, 'Category__c': None,
                 'Customer_Name__c': 'A', 'Process_Add_Info_1__c': 'X',
                 'Process_Add_Info_2__c': 'Y', 'Process_Add_Info_3__c': None,
                 'Process_Add_Info_4__c': None, 'Process_Add_Info_9__c': '1234567890123',
                 'ContactId': None, 'AccountId': None},
                {'Id': 'ID2', 'CaseNumber': '002', 'Subject': 'S2', 'Type__c': 'T2',
                 'Status': 'Open', 'Sub_Status__c': None, 'Category__c': None,
                 'Customer_Name__c': 'B', 'Process_Add_Info_1__c': None,
                 'Process_Add_Info_2__c': None, 'Process_Add_Info_3__c': None,
                 'Process_Add_Info_4__c': None, 'Process_Add_Info_9__c': None,
                 'ContactId': None, 'AccountId': None},
            ],
        }

        cases = extractor.extract()
        assert len(cases) == 2
        assert cases[0].case_number == '001'
        assert cases[1].case_number == '002'


class TestExtractRetry:
    """Tests for retry logic."""

    def test_retries_on_timeout(self, extractor, mock_sf):
        mock_sf.query.side_effect = [
            TimeoutError("Connection timed out"),
            TimeoutError("Connection timed out"),
            {'totalSize': 0, 'records': []},
        ]

        cases = extractor.extract()

        assert cases == []
        assert mock_sf.query.call_count == 3

    def test_raises_after_max_retries(self, extractor, mock_sf):
        mock_sf.query.side_effect = TimeoutError("Connection timed out")

        with pytest.raises(ExtractionError, match="Failed after 3 retries"):
            extractor.extract()

        assert mock_sf.query.call_count == MAX_RETRIES

    def test_retries_on_server_error(self, extractor, mock_sf):
        mock_sf.query.side_effect = [
            Exception("HTTP 500 Internal Server Error"),
            Exception("HTTP 500 Internal Server Error"),
            {'totalSize': 1, 'records': [{
                'Id': 'ID1', 'CaseNumber': '001', 'Subject': 'S', 'Type__c': 'T',
                'Status': 'Open', 'Sub_Status__c': None, 'Category__c': None,
                'Customer_Name__c': None, 'Process_Add_Info_1__c': None,
                'Process_Add_Info_2__c': None, 'Process_Add_Info_3__c': None,
                'Process_Add_Info_4__c': None, 'Process_Add_Info_9__c': None,
                'ContactId': None, 'AccountId': None,
            }]},
            {'totalSize': 0, 'records': []},  # attachments query
            {'totalSize': 0, 'records': []},  # content docs query
        ]

        cases = extractor.extract()
        assert len(cases) == 1
        # 2 failed + 1 success + 2 doc queries = 5 total
        assert mock_sf.query.call_count == 5


class TestExtractAuthFailure:
    """Tests for authentication failure (no retry)."""

    def test_auth_failure_raises_immediately(self, extractor, mock_sf):
        mock_sf.query.side_effect = SalesforceAuthenticationFailed(
            500, "INVALID_LOGIN"
        )

        with pytest.raises(ExtractionError, match="auth failed"):
            extractor.extract()

        # Should NOT retry on auth failure
        assert mock_sf.query.call_count == 1


class TestExtractDocuments:
    """Tests for document fetching."""

    def test_fetches_attachments(self, extractor, mock_sf):
        # First call: main query
        mock_sf.query.side_effect = [
            {'totalSize': 1, 'records': [{
                'Id': 'CASE1', 'CaseNumber': '001', 'Subject': 'S', 'Type__c': 'T',
                'Status': 'Open', 'Sub_Status__c': None, 'Category__c': None,
                'Customer_Name__c': None, 'Process_Add_Info_1__c': None,
                'Process_Add_Info_2__c': None, 'Process_Add_Info_3__c': None,
                'Process_Add_Info_4__c': None, 'Process_Add_Info_9__c': None,
                'ContactId': None, 'AccountId': None,
            }]},
            # Second call: attachments query
            {'totalSize': 1, 'records': [{
                'Id': 'ATT1', 'Name': 'ID_Card.pdf', 'ContentType': 'application/pdf',
                'BodyLength': 150000, 'CreatedDate': '2024-01-01',
            }]},
            # Third call: content docs query
            {'totalSize': 0, 'records': []},
        ]

        cases = extractor.extract()

        assert len(cases) == 1
        assert len(cases[0].verification_documents) == 1
        assert cases[0].verification_documents[0].name == 'ID_Card.pdf'
        assert cases[0].verification_documents[0].size_bytes == 150000

    def test_no_documents_returns_empty_list(self, extractor, mock_sf):
        mock_sf.query.side_effect = [
            {'totalSize': 1, 'records': [{
                'Id': 'CASE1', 'CaseNumber': '001', 'Subject': 'S', 'Type__c': 'T',
                'Status': 'Open', 'Sub_Status__c': None, 'Category__c': None,
                'Customer_Name__c': None, 'Process_Add_Info_1__c': None,
                'Process_Add_Info_2__c': None, 'Process_Add_Info_3__c': None,
                'Process_Add_Info_4__c': None, 'Process_Add_Info_9__c': None,
                'ContactId': None, 'AccountId': None,
            }]},
            {'totalSize': 0, 'records': []},  # attachments
            {'totalSize': 0, 'records': []},  # content docs
        ]

        cases = extractor.extract()
        assert cases[0].verification_documents == []
