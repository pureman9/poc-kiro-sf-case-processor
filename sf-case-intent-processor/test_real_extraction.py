"""Test real extraction from Salesforce sandbox using updated field mapping."""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))
load_dotenv()

from config import load_config
from sf_case_extractor.extractor import SFCaseExtractor
from shared.logger import setup_logger

def main():
    setup_logger(level="INFO")
    config = load_config()

    print("=" * 70)
    print("REAL EXTRACTION TEST — Salesforce Sandbox")
    print("=" * 70)

    extractor = SFCaseExtractor(config)

    # Fetch cases (include closed for testing since most cases are closed)
    cases = extractor.extract(include_closed=True, limit=5)

    print(f"\n✅ Extracted {len(cases)} cases\n")

    for i, case in enumerate(cases, 1):
        print(f"--- Case {i} ---")
        print(f"  Case #:        {case.case_number}")
        print(f"  Subject:       {case.subject}")
        print(f"  Intent Type:   {case.intent_type}")
        print(f"  Status:        {case.status} / {case.sub_status}")
        print(f"  Customer:      {case.customer_name}")
        print(f"  Citizen ID:    {case.cid}")
        print(f"  New First:     {case.new_first_name}")
        print(f"  New Last:      {case.new_last_name}")
        print(f"  New Title:     {case.new_title}")
        print(f"  Old Name:      {case.old_name}")
        print(f"  Documents:     {len(case.verification_documents)}")
        for doc in case.verification_documents:
            print(f"    - {doc.name} ({doc.content_type}, {doc.size_bytes} bytes)")
        print()


if __name__ == "__main__":
    main()
