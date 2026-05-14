"""Test Mobius API connection — search customer by CID."""

import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from mobius_client.client import MobiusClient

def main():
    client = MobiusClient()

    # Test with CID from SF case #00001659
    test_cid = "9280635310483"

    print("=" * 60)
    print(f"  Mobius API Connection Test")
    print(f"  Searching customer by CID: {test_cid}")
    print("=" * 60)

    result = client.search_customer_by_cid(test_cid)

    print(f"\n  OK: {result.ok}")
    print(f"  Status Code: {result.status_code}")
    print(f"  Customer ID (CIF): {result.customer_id}")
    print(f"  Message: {result.message}")

    if result.ok and result.data:
        profiles = result.data.get("data", {}).get("profileList", [])
        if profiles:
            p = profiles[0]
            print(f"\n  --- Customer Profile ---")
            print(f"  CIF:           {p.get('customerId')}")
            print(f"  Title:         {p.get('titleCode')}")
            print(f"  Thai Name:     {p.get('thaiFirstName')} {p.get('thaiLastName')}")
            print(f"  Eng Name:      {p.get('engFirstName')} {p.get('engLastName')}")
            print(f"  DOB:           {p.get('birthDate')}")
            print(f"  Gender:        {p.get('genderCode')}")
            print(f"  Nationality:   {p.get('nationalityCode')}")
            contacts = p.get('primaryContact', [])
            for c in contacts:
                print(f"  Contact ({c.get('contactTypeCode')}): {c.get('contactInformation')}")
    else:
        print(f"\n  ❌ Failed: {result.message}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
