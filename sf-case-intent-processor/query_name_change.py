"""Query specifically for name change intent cases."""
import os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from simple_salesforce import Salesforce

sf = Salesforce(username=os.getenv('SF_USERNAME'), password=os.getenv('SF_PASSWORD'), security_token='', domain='test')

result = sf.query(
    "SELECT Id, CaseNumber, Subject, Type__c, Status, Sub_Status__c, "
    "Customer_Name__c, Process_Add_Info_1__c, Process_Add_Info_2__c, "
    "Process_Add_Info_3__c, Process_Add_Info_4__c, Process_Add_Info_9__c "
    "FROM Case "
    "WHERE Type__c LIKE 'CC - %เปลี่ยนแปลง%' "
    "LIMIT 10"
)

print(f"Cases with name/title change intent: {result['totalSize']}\n")
for r in result['records']:
    print(f"  #{r['CaseNumber']} | {r['Type__c']}")
    print(f"    Status: {r['Status']} / {r.get('Sub_Status__c', '-')}")
    print(f"    Customer: {r.get('Customer_Name__c', '?')}")
    print(f"    New First: {r.get('Process_Add_Info_1__c', '-')}")
    print(f"    New Last:  {r.get('Process_Add_Info_2__c', '-')}")
    print(f"    New Title: {r.get('Process_Add_Info_3__c', '-')}")
    print(f"    Old Name:  {r.get('Process_Add_Info_4__c', '-')}")
    print(f"    Citizen ID: {r.get('Process_Add_Info_9__c', '-')}")
    print()
