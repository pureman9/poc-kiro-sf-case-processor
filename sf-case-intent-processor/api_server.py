"""Minimal local API server for the Call Center UI.

Provides endpoints that query Salesforce sandbox and return cases as JSON.
Run: python api_server.py
Then the UI can call http://localhost:5000/api/cases
"""

import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse
import threading

sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from config import load_config
from sf_case_extractor.extractor import SFCaseExtractor

PORT = 5000
config = load_config()
extractor = None
extractor_lock = threading.Lock()


def get_extractor():
    """Lazy-initialize extractor on first API call (thread-safe)."""
    global extractor
    if extractor is None:
        with extractor_lock:
            if extractor is None:
                extractor = SFCaseExtractor(config)
    return extractor


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in separate threads so one slow query doesn't block all."""
    daemon_threads = True


class APIHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler with CORS support."""

    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == '/api/cases':
            self._handle_cases()
        elif path == '/api/health':
            self._respond(200, {"status": "ok", "port": PORT})
        else:
            self._respond(404, {"error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path

        if path == '/api/submit':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}
            self._handle_submit(data)
        else:
            self._respond(404, {"error": "Not found"})

    def _handle_cases(self):
        try:
            ext = get_extractor()
            # Use direct SOQL query without fetching attachments per case (faster)
            from sf_case_extractor.soql_builder import build_ciu_query
            sf = ext._connect()
            soql = build_ciu_query(include_closed=False, limit=100)
            result = sf.query(soql)

            ui_cases = []
            for record in result.get('records', []):
                ui_cases.append({
                    "caseId": record.get('Id', ''),
                    "caseNumber": record.get('CaseNumber', ''),
                    "subject": record.get('Subject', ''),
                    "intentType": record.get('Type__c', ''),
                    "status": record.get('Status', ''),
                    "subStatus": record.get('Sub_Status__c', ''),
                    "category": record.get('Category__c', ''),
                    "customerName": record.get('Customer_Name__c', ''),
                    "citizenId": record.get('Process_Add_Info_9__c', ''),
                    "newFirstName": record.get('Process_Add_Info_1__c', ''),
                    "newLastName": record.get('Process_Add_Info_2__c', ''),
                    "newTitle": record.get('Process_Add_Info_3__c', ''),
                    "oldName": record.get('Process_Add_Info_4__c', ''),
                    "documents": [],
                })
            self._respond(200, {"cases": ui_cases, "count": len(ui_cases)})
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _handle_submit(self, data):
        """Handle case submission: Mobius sync + SF case close."""
        try:
            from mobius_client.client import MobiusClient
            from mobius_client.models import thai_title_to_mobius_code
            from sf_case_extractor.case_updater import SFCaseUpdater

            case_id = data.get("caseId", "")
            citizen_id = data.get("citizenId", "")
            intent_type = data.get("intentType", "")
            new_values = data.get("newValues", {})

            results = {"steps": []}

            # Step 1: Search CIF by CID (if citizen ID available)
            mobius = MobiusClient()
            customer_id = None

            if citizen_id and citizen_id != "—":
                search = mobius.search_customer_by_cid(citizen_id)
                if search.ok:
                    customer_id = search.customer_id
                    results["steps"].append({"step": "Search CIF", "ok": True, "cif": customer_id})
                else:
                    results["steps"].append({"step": "Search CIF", "ok": False, "error": search.message})
            else:
                results["steps"].append({"step": "Search CIF", "ok": False, "error": "No citizen ID"})

            # Step 2: Update Mobius based on intent
            if customer_id:
                if "thaiFirstName" in new_values or "thaiLastName" in new_values:
                    # Name update
                    r = mobius.update_customer_name(
                        customer_id=customer_id,
                        title_code=new_values.get("titleCode"),
                        thai_first_name=new_values.get("thaiFirstName"),
                        thai_last_name=new_values.get("thaiLastName"),
                        eng_first_name=new_values.get("engFirstName"),
                        eng_last_name=new_values.get("engLastName"),
                    )
                    results["steps"].append({"step": "Mobius Update Name", "ok": r.ok, "message": r.message})

                elif "titleCode" in new_values:
                    # Title update
                    r = mobius.update_customer_name(
                        customer_id=customer_id,
                        title_code=new_values.get("titleCode"),
                    )
                    results["steps"].append({"step": "Mobius Update Title", "ok": r.ok, "message": r.message})

                elif "addressNumber" in new_values:
                    # Address update
                    r = mobius.update_customer_address(
                        customer_id=customer_id,
                        address_number=new_values.get("addressNumber", ""),
                        moo=new_values.get("moo", ""),
                        soi=new_values.get("soi", ""),
                        thanon=new_values.get("thanon", ""),
                        sub_district=new_values.get("subDistrict", ""),
                        district=new_values.get("district", ""),
                        province=new_values.get("province", ""),
                        zip_code=new_values.get("zipCode", ""),
                    )
                    results["steps"].append({"step": "Mobius Update Address", "ok": r.ok, "message": r.message})

                elif "contactPhone" in new_values:
                    # Phone update
                    r = mobius.update_customer_phone(customer_id, new_values["contactPhone"])
                    results["steps"].append({"step": "Mobius Update Phone", "ok": r.ok, "message": r.message})

                elif "contactEmail" in new_values:
                    # Email update
                    r = mobius.update_customer_email(customer_id, new_values["contactEmail"])
                    results["steps"].append({"step": "Mobius Update Email", "ok": r.ok, "message": r.message})

            # Step 3: Close SF case
            if case_id:
                try:
                    ext = get_extractor()
                    sf = ext._connect()
                    updater = SFCaseUpdater(sf)
                    closed = updater.close_case(case_id, sub_status="Done")
                    results["steps"].append({"step": "Close SF Case", "ok": closed})
                except Exception as e:
                    results["steps"].append({"step": "Close SF Case", "ok": False, "error": str(e)})

            all_ok = all(s.get("ok", False) for s in results["steps"])
            results["success"] = all_ok
            self._respond(200, results)

        except Exception as e:
            self._respond(500, {"error": str(e), "success": False})

    def _respond(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        print(f"[API] {args[0]}")


def main():
    server = ThreadedHTTPServer(('localhost', PORT), APIHandler)
    print(f"=" * 50)
    print(f"  SF Case API Server running on http://localhost:{PORT}")
    print(f"  Endpoints:")
    print(f"    GET /api/cases  — fetch non-closed cases from Salesforce")
    print(f"    GET /api/health — server health check")
    print(f"  Press Ctrl+C to stop")
    print(f"=" * 50)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
