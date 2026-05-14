"""SOQL query builder for Customer Information Update cases — real sandbox schema."""

from intents.personal_info_change.field_map import SUPPORTED_INTENTS, get_all_intent_type_prefixes


def build_ciu_query(
    intent_types: list[str] | None = None,
    include_closed: bool = False,
    limit: int | None = None,
) -> str:
    """Build a SOQL query to fetch Customer Information Update cases.

    Dynamically builds WHERE clause from registered intents in field_map.py.
    Adding a new intent to INTENT_FIELD_MAP automatically includes it in queries.

    Args:
        intent_types: Specific Type__c values to filter. None = all registered intents.
        include_closed: If True, include closed cases (for testing). Default False.
        limit: Max records to return. None = no limit.

    Returns:
        A SOQL query string ready to execute via simple_salesforce.
    """
    # Use provided list or all registered intents
    types_to_query = intent_types or SUPPORTED_INTENTS
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

    where_clauses = []

    # Build intent filter — use IN clause for multiple intents
    if len(types_to_query) == 1:
        where_clauses.append(f"Type__c = '{types_to_query[0]}'")
    else:
        # Use OR with LIKE for each prefix to cover all sub-intents
        prefixes = get_all_intent_type_prefixes()
        prefix_conditions = [f"Type__c LIKE '{p}%'" for p in prefixes]
        where_clauses.append(f"({' OR '.join(prefix_conditions)})")

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
