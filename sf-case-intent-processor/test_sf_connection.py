"""Test Salesforce sandbox connection and explore Case schema."""

import os
from dotenv import load_dotenv
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed

load_dotenv()

def main():
    username = os.getenv("SF_USERNAME")
    password = os.getenv("SF_PASSWORD")
    token    = os.getenv("SF_SECURITY_TOKEN", "")
    domain   = os.getenv("SF_DOMAIN", "test")

    print(f"Connecting to Salesforce sandbox...")
    print(f"  Username: {username}")
    print(f"  Domain:   {domain}")
    print(f"  Token:    {'(provided)' if token else '(empty — relying on trusted IP)'}")
    print()

    try:
        sf = Salesforce(
            username=username,
            password=password,
            security_token=token,
            domain=domain,
        )
        print(f"✅ Connected successfully!")
        print(f"  Instance URL: {sf.sf_instance}")
        print(f"  Session ID:   {sf.session_id[:20]}...")
        print()

        # Describe Case object to find field names
        print("=" * 60)
        print("CASE OBJECT — Field Names")
        print("=" * 60)
        case_desc = sf.Case.describe()
        fields = case_desc['fields']

        # Print all fields (looking for CID, Intent, etc.)
        print(f"\nTotal fields: {len(fields)}")
        print("\nCustom fields (ending with __c):")
        print("-" * 60)
        custom_fields = [f for f in fields if f['name'].endswith('__c')]
        for f in sorted(custom_fields, key=lambda x: x['name']):
            print(f"  {f['name']:40s} | {f['type']:15s} | {f['label']}")

        print("\n\nStandard fields (key ones):")
        print("-" * 60)
        key_standard = ['Id', 'CaseNumber', 'Status', 'Subject', 'Description', 'ContactId', 'AccountId', 'Type', 'Reason', 'Origin']
        for fname in key_standard:
            f = next((x for x in fields if x['name'] == fname), None)
            if f:
                print(f"  {f['name']:40s} | {f['type']:15s} | {f['label']}")

        # Check for child relationships (related lists)
        print("\n\nChild Relationships (related lists):")
        print("-" * 60)
        for rel in case_desc.get('childRelationships', []):
            if rel.get('relationshipName'):
                print(f"  {rel['relationshipName']:40s} | {rel['childSObject']}")

        # Try a simple query
        print("\n\n" + "=" * 60)
        print("SAMPLE QUERY — First 5 non-closed cases")
        print("=" * 60)
        result = sf.query("SELECT Id, CaseNumber, Status, Subject FROM Case WHERE Status != 'Closed' LIMIT 5")
        print(f"\nTotal records: {result['totalSize']}")
        for record in result['records']:
            print(f"  {record['Id'][:15]}... | #{record['CaseNumber']} | {record['Status']:10s} | {record.get('Subject', '(no subject)')}")

    except SalesforceAuthenticationFailed as e:
        print(f"❌ Authentication failed: {e}")
        print("\nPossible fixes:")
        print("  1. Check username/password")
        print("  2. Get Security Token: Salesforce → Settings → Reset My Security Token")
        print("  3. Add your IP to trusted IP ranges in Salesforce Setup")
        print("  4. For sandbox, username might need '.uat' suffix: manuchet@cardx.co.th.uat")
    except Exception as e:
        print(f"❌ Connection error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
