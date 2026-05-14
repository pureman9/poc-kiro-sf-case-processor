"""Test Mobius with CID 3106043294145."""
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from mobius_client.client import MobiusClient

client = MobiusClient()
result = client.search_customer_by_cid("3106043294145")
print(f"OK: {result.ok}")
print(f"CIF: {result.customer_id}")
print(f"Status: {result.status_code}")
print(f"Message: {result.message}")
if result.ok and result.data:
    profiles = result.data.get("data", {}).get("profileList", [])
    if profiles:
        p = profiles[0]
        print(f"Title: {p.get('titleCode')}")
        print(f"Thai: {p.get('thaiFirstName')} {p.get('thaiLastName')}")
        print(f"Eng: {p.get('engFirstName')} {p.get('engLastName')}")
        print(f"DOB: {p.get('birthDate')}")
        for c in p.get("primaryContact", []):
            print(f"Contact ({c.get('contactTypeCode')}): {c.get('contactInformation')}")
