"""SOQL query builder for Customer Information Update cases — real sandbox schema."""

# Intent type prefix for Customer Information Update category
DEFAULT_INTENT_TYPE_PREFIX = "CC - ข้อมูลส่วนตัว"

# Specific intent type for name change (scope: this intent only)
INTENT_NAME_CHANGE = "CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล"

# Category value for personal data management
CATEGORY_PERSONAL_DATA = "การจัดการข้อมูลส่วนบุคคล"


def build_ciu_query(
    intent_type: str = INTENT_NAME_CHANGE,
    include_closed: bool = False,
    limit: int | None = None,
) -> str:
    """Build a SOQL query to fetch Customer Information Update cases.

    Scoped to: CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล only.

    Real Salesforce field mapping (from Case #00001659):
        - Subject: full intent string
        - Type__c: "CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล"
        - Process_Add_Info_1__c: new first name
        - Process_Add_Info_2__c: new last name
        - Process_Add_Info_3__c: new title
        - Process_Add_Info_4__c: old name
        - Process_Add_Info_9__c: citizen ID (13 digits)

    Args:
        intent_type: Exact Type__c value to filter. Default: name change intent.
        include_closed: If True, include closed cases (for testing). Default False.
        limit: Max records to return. None = no limit.

    Returns:
        A SOQL query string ready to execute via simple_salesforce.
    """
    fields = [
        "Id",
        "CaseNumber",
        "Subject",
        "Type__c",
        "Status",
        "Sub_Status__c",
        "Category__c",
        "L2_Category__c",
        "Priority",
        "Origin",
        "Customer_Name__c",
        "Citizen_ID_Ano__c",
        "Process_Add_Info_1__c",   # New first name
        "Process_Add_Info_2__c",   # New last name
        "Process_Add_Info_3__c",   # New title
        "Process_Add_Info_4__c",   # Old name
        "Process_Add_Info_5__c",   # Contact channel
        "Process_Add_Info_6__c",   # Phone
        "Process_Add_Info_9__c",   # Citizen ID
        "Case_Outcome__c",
        "ContactId",
        "AccountId",
        "CreatedDate",
        "ClosedDate",
    ]

    where_clauses = [
        f"Type__c = '{intent_type}'",
    ]

    if not include_closed:
        where_clauses.append("Status != 'Closed'")

    query = (
        f"SELECT {', '.join(fields)} "
        f"FROM Case "
        f"WHERE {' AND '.join(where_clauses)}"
    )

    if limit:
        query += f" LIMIT {limit}"

    return query


def build_case_attachments_query(case_id: str) -> str:
    """Build a SOQL query to fetch attachments for a specific case.

    Args:
        case_id: The Salesforce Case Id.

    Returns:
        SOQL query for Attachment records.
    """
    return (
        f"SELECT Id, Name, ContentType, BodyLength, CreatedDate "
        f"FROM Attachment "
        f"WHERE ParentId = '{case_id}'"
    )


def build_case_content_docs_query(case_id: str) -> str:
    """Build a SOQL query to fetch ContentDocumentLinks for a specific case.

    Args:
        case_id: The Salesforce Case Id.

    Returns:
        SOQL query for ContentDocumentLink records.
    """
    return (
        f"SELECT ContentDocumentId, ContentDocument.Title, "
        f"ContentDocument.FileType, ContentDocument.ContentSize "
        f"FROM ContentDocumentLink "
        f"WHERE LinkedEntityId = '{case_id}'"
    )
