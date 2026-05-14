"""SOQL query builder for Customer Information Update cases."""

# Default intent prefix for Customer Information Update category
DEFAULT_INTENT_PREFIX = "ขอใช้บริการ:CC - ข้อมูลส่วนตัว"


def build_ciu_query(intent_prefix: str = DEFAULT_INTENT_PREFIX) -> str:
    """Build a SOQL query to fetch non-closed Customer Information Update cases.

    Args:
        intent_prefix: The intent name prefix to filter on.
                       Default: 'ขอใช้บริการ:CC - ข้อมูลส่วนตัว'

    Returns:
        A SOQL query string ready to execute via simple_salesforce.
    """
    return (
        "SELECT Id, CID__c, Intent_Name__c, Status, New_Value__c, "
        "(SELECT Id, Status__c FROM VerificationDocuments__r) "
        "FROM Case "
        "WHERE Status != 'Closed' "
        f"AND Intent_Name__c LIKE '{intent_prefix}%'"
    )
