"""Query Case #00001659 to see all field values and understand the data structure."""

import os
import json
from dotenv import load_dotenv
from simple_salesforce import Salesforce

load_dotenv()

def main():
    sf = Salesforce(
        username=os.getenv("SF_USERNAME"),
        password=os.getenv("SF_PASSWORD"),
        security_token=os.getenv("SF_SECURITY_TOKEN", ""),
        domain=os.getenv("SF_DOMAIN", "test"),
    )

    print("=" * 70)
    print("QUERY: Case #00001659 — เปลี่ยนแปลงชื่อ-นามสกุล")
    print("=" * 70)

    # Query all fields for this specific case
    query = """
        SELECT Id, CaseNumber, Status, Sub_Status__c, Subject, Priority,
               Origin, Type, Type__c, Category__c, L2_Category__c,
               Intent__c, Intent_Unique_Name__c, Intent_Description__c,
               Customer_Name__c, Citizen_ID_Ano__c, Citizen_Passport_Alien_Id__c,
               Customer_Email__c, CustomerSegment__c, Customer_Language__c,
               Product__c, Product_Type__c, Product_Group__c, Product_Number__c,
               Process_Add_Info_1__c, Process_Add_Info_2__c, Process_Add_Info_3__c,
               Process_Add_Info_4__c, Process_Add_Info_5__c, Process_Add_Info_6__c,
               Process_Add_Info_7__c, Process_Add_Info_8__c, Process_Add_Info_9__c,
               Process_Add_Info_10__c, Process_Add_Info_11__c, Process_Add_Info_12__c,
               Process_Add_Info_14__c, Process_Add_Info_15__c,
               Remark__c, Service_Text__c, Topic__c,
               Case_Outcome__c, FU_Reason__c, FU_Document_and_Reason__c,
               ContactId, AccountId, CreatedDate, ClosedDate
        FROM Case
        WHERE CaseNumber = '00001659'
    """

    result = sf.query(query)
    print(f"\nRecords found: {result['totalSize']}")

    if result['totalSize'] == 0:
        print("No case found with this number.")
        return

    case = result['records'][0]

    print("\n--- ALL FIELD VALUES (non-null only) ---\n")
    for key, value in sorted(case.items()):
        if key == 'attributes':
            continue
        if value is not None and value != '':
            print(f"  {key:45s} = {value}")

    # Also check attachments / content documents
    case_id = case['Id']
    print(f"\n\n--- ATTACHMENTS for Case {case_id} ---\n")
    att_query = f"SELECT Id, Name, ContentType, BodyLength, CreatedDate FROM Attachment WHERE ParentId = '{case_id}'"
    att_result = sf.query(att_query)
    print(f"Attachments: {att_result['totalSize']}")
    for att in att_result['records']:
        print(f"  {att['Name']:40s} | {att['ContentType']:20s} | {att['BodyLength']} bytes | {att['CreatedDate']}")

    # Content Document Links
    print(f"\n--- CONTENT DOCUMENTS for Case {case_id} ---\n")
    cdl_query = f"SELECT ContentDocumentId, ContentDocument.Title, ContentDocument.FileType, ContentDocument.ContentSize FROM ContentDocumentLink WHERE LinkedEntityId = '{case_id}'"
    try:
        cdl_result = sf.query(cdl_query)
        print(f"Content Documents: {cdl_result['totalSize']}")
        for cdl in cdl_result['records']:
            doc = cdl.get('ContentDocument', {})
            print(f"  {doc.get('Title','?'):40s} | {doc.get('FileType','?'):10s} | {doc.get('ContentSize',0)} bytes")
    except Exception as e:
        print(f"  (Could not query ContentDocumentLink: {e})")

    # Check the Intent lookup object
    intent_id = case.get('Intent__c')
    if intent_id:
        print(f"\n\n--- INTENT OBJECT (Id: {intent_id}) ---\n")
        try:
            intent_query = f"SELECT Id, Name, Intent_Unique_Name__c FROM Customer_Intent__c WHERE Id = '{intent_id}'"
            intent_result = sf.query(intent_query)
            if intent_result['totalSize'] > 0:
                intent = intent_result['records'][0]
                for k, v in intent.items():
                    if k != 'attributes' and v:
                        print(f"  {k:40s} = {v}")
        except Exception as e:
            # Try generic describe
            print(f"  (Could not query Intent object: {e})")
            # Try querying with just the reference
            try:
                intent_desc = sf.query(f"SELECT Id, Name FROM Customer_Intent__c WHERE Id = '{intent_id}'")
                for r in intent_desc['records']:
                    print(f"  {r}")
            except:
                pass


if __name__ == "__main__":
    main()
