"""Minimal local API server for the Call Center UI.

Provides a single endpoint that queries Salesforce sandbox and returns cases as JSON.
Run: python api_server.py
Then the UI can call http://localhost:5000/api/cases
"""

import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from config import load_config
from sf_case_extractor.extractor import SFCaseExtractor

PORT = 5000
config = load_config()
extractor = SFCaseExtractor(config)


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

    def _handle_cases(self):
        try:
            cases = extractor.extract(include_closed=False)
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
            self._respond(200, {"cases": ui_cases, "count": len(ui_cases)})
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _respond(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        print(f"[API] {args[0]}")


def main():
    server = HTTPServer(('localhost', PORT), APIHandler)
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
