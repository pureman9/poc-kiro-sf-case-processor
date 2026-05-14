"""Unit tests for SOQL query builder."""

from sf_case_extractor.soql_builder import build_ciu_query, DEFAULT_INTENT_PREFIX


class TestBuildCiuQuery:
    """Tests for build_ciu_query() function."""

    def test_default_query_contains_status_filter(self):
        query = build_ciu_query()
        assert "Status != 'Closed'" in query

    def test_default_query_contains_intent_filter(self):
        query = build_ciu_query()
        assert f"Intent_Name__c LIKE '{DEFAULT_INTENT_PREFIX}%'" in query

    def test_default_query_selects_required_fields(self):
        query = build_ciu_query()
        assert "Id" in query
        assert "CID__c" in query
        assert "Intent_Name__c" in query
        assert "Status" in query
        assert "New_Value__c" in query

    def test_default_query_includes_verification_documents_subquery(self):
        query = build_ciu_query()
        assert "VerificationDocuments__r" in query
        assert "Status__c" in query

    def test_custom_intent_prefix(self):
        custom_prefix = "Custom:Intent:Prefix"
        query = build_ciu_query(intent_prefix=custom_prefix)
        assert f"Intent_Name__c LIKE '{custom_prefix}%'" in query
        assert DEFAULT_INTENT_PREFIX not in query

    def test_query_is_single_string(self):
        query = build_ciu_query()
        assert isinstance(query, str)
        assert len(query) > 50  # Sanity check — not empty

    def test_query_from_case_table(self):
        query = build_ciu_query()
        assert "FROM Case" in query
