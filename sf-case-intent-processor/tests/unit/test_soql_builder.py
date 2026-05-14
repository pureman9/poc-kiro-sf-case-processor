"""Unit tests for SOQL query builder."""

from sf_case_extractor.soql_builder import build_ciu_query
from intents.personal_info_change.field_map import SUPPORTED_INTENTS


class TestBuildCiuQuery:
    """Tests for build_ciu_query() function."""

    def test_default_query_contains_status_filter(self):
        query = build_ciu_query()
        assert "Status != 'Closed'" in query

    def test_default_query_contains_intent_filter(self):
        query = build_ciu_query()
        assert "Type__c LIKE 'CC - ข้อมูลส่วนตัว%'" in query

    def test_default_query_selects_required_fields(self):
        query = build_ciu_query()
        assert "Id" in query
        assert "CaseNumber" in query
        assert "Type__c" in query
        assert "Status" in query
        assert "Process_Add_Info_1__c" in query

    def test_include_closed_removes_status_filter(self):
        query = build_ciu_query(include_closed=True)
        assert "Status != 'Closed'" not in query

    def test_limit_parameter(self):
        query = build_ciu_query(limit=10)
        assert "LIMIT 10" in query

    def test_no_limit_by_default(self):
        query = build_ciu_query()
        assert "LIMIT" not in query

    def test_single_intent_uses_exact_match(self):
        query = build_ciu_query(intent_types=["CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล"])
        assert "Type__c = 'CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล'" in query

    def test_query_from_case_table(self):
        query = build_ciu_query()
        assert "FROM Case" in query

    def test_does_not_include_new_card_intent(self):
        query = build_ciu_query()
        assert "ขอบัตรใหม่" not in query
