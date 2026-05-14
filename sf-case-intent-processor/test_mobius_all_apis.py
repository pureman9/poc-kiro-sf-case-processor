"""Test ALL Mobius API endpoints with CIF 690153117 (CID 3106043294145)."""
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from mobius_client.client import MobiusClient

client = MobiusClient()
CIF = "690153117"  # From search result

print("=" * 60)
print("  Mobius API — Full Integration Test")
print("  CIF:", CIF)
print("=" * 60)

# ── Test 1: PUT /party/cust-profile (Update Name/Title) ───────────────────────
print("\n[1] PUT /party/cust-profile — Update Name")
result = client.update_customer_name(
    customer_id=CIF,
    title_code="MISS",
    thai_first_name="แอนนา",
    thai_last_name="นาวิต้า",
    eng_first_name="ANNA",
    eng_last_name="NAVITA",
)
print(f"    OK: {result.ok}")
print(f"    Status: {result.status_code}")
print(f"    Message: {result.message}")
if result.data:
    print(f"    Response: {str(result.data)[:200]}")

# ── Test 2: POST /party/cust-profile/address (Update Address) ─────────────────
print("\n[2] POST /party/cust-profile/address — Update Address")
result = client.update_customer_address(
    customer_id=CIF,
    address_number="66/8",
    moo="2",
    soi="Ari 23",
    thanon="Ratchadaphisek",
    sub_district="Chatuchak",
    district="Chatuchak",
    province="Bangkok",
    zip_code="10150",
    country="TH",
    address_type="A",
    address_format="L",
)
print(f"    OK: {result.ok}")
print(f"    Status: {result.status_code}")
print(f"    Message: {result.message}")
if result.data:
    print(f"    Response: {str(result.data)[:200]}")

# ── Test 3: POST /party/cust-profile/{cif}/Contacts — Phone ──────────────────
print("\n[3] POST /party/cust-profile/{cif}/Contacts — Update Phone")
result = client.update_customer_phone(CIF, "0891234567")
print(f"    OK: {result.ok}")
print(f"    Status: {result.status_code}")
print(f"    Message: {result.message}")
if result.data:
    print(f"    Response: {str(result.data)[:200]}")

# ── Test 4: POST /party/cust-profile/{cif}/Contacts — Email ──────────────────
print("\n[4] POST /party/cust-profile/{cif}/Contacts — Update Email")
result = client.update_customer_email(CIF, "test_update@cardx.co.th")
print(f"    OK: {result.ok}")
print(f"    Status: {result.status_code}")
print(f"    Message: {result.message}")
if result.data:
    print(f"    Response: {str(result.data)[:200]}")

print("\n" + "=" * 60)
print("  Test Complete")
print("=" * 60)
