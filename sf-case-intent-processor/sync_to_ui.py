"""Sync Salesforce cases to UI JSON file.

Fetches non-closed 'เปลี่ยนแปลงชื่อ-นามสกุล' cases from sandbox
and writes them to Case_Update_Name/sf_cases.json for the UI to consume.
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from config import load_config
from sf_case_extractor.extractor import SFCaseExtractor


def main():
    config = load_config()
    extractor = SFCaseExtractor(config)

    print("Fetching cases from Salesforce sandbox...")
    cases = extractor.extract(include_closed=False)
    print(f"Found {len(cases)} non-closed cases")

    # Convert to JSON-serializable format for the UI
    ui_cases = []
    for case in cases:
        ui_cases.append({
            "caseId": case.case_id,
            "caseNumber": case.case_number,
            "subject": case.subject,
            "intentType": case.intent_type,
            "status": case.status,
            "subStatus": case.sub_status,
            "category": case.category,
            "customerName": case.customer_name,
            "citizenId": case.citizen_id,
            "newFirstName": case.new_first_name,
            "newLastName": case.new_last_name,
            "newTitle": case.new_title,
            "oldName": case.old_name,
            "documents": [
                {"id": d.doc_id, "name": d.name, "type": d.content_type, "size": d.size_bytes}
                for d in case.verification_documents
            ],
        })

    # Write to UI folder
    output_path = Path(__file__).parent.parent / "Case_Update_Name" / "sf_cases.json"
    output_path.write_text(json.dumps(ui_cases, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written to: {output_path}")
    print(f"\nCases exported:")
    for c in ui_cases:
        print(f"  #{c['caseNumber']} | {c['status']} | {c['customerName']} | New: {c['newFirstName']} {c['newLastName']}")


if __name__ == "__main__":
    main()
