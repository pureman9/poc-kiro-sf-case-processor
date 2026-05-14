"""Test scoped extraction: only 'CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล'."""
import os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from config import load_config
from sf_case_extractor.extractor import SFCaseExtractor

def main():
    config = load_config()
    extractor = SFCaseExtractor(config)

    # Include closed to see the one case we know exists (#00001659)
    cases = extractor.extract(include_closed=True, limit=10)

    print(f"Cases matching 'CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล': {len(cases)}\n")

    for case in cases:
        print(f"  #{case.case_number} | {case.intent_type}")
        print(f"    Status:    {case.status} / {case.sub_status}")
        print(f"    Customer:  {case.customer_name}")
        print(f"    Citizen ID:{case.cid}")
        print(f"    New First: {case.new_first_name}")
        print(f"    New Last:  {case.new_last_name}")
        print(f"    New Title: {case.new_title}")
        print(f"    Old Name:  {case.old_name}")
        print(f"    Docs:      {len(case.verification_documents)}")
        print()

if __name__ == "__main__":
    main()
