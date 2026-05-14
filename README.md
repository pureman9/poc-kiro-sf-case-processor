# SF Case Intent Processor — POC

A Salesforce call center UI prototype for processing Customer Information Update cases.  
Built with HTML / CSS / JavaScript (no framework, no server required).

## Features

- **Case Processing** — 4-step flow: select intent → enter new value → upload & verify document → confirm & submit
- **6 Intent Types** — First name, last name, title, full name, national ID, date of birth
- **Approval Routing** — Auto-approve / Operations Team / Compliance Team based on intent risk level
- **OCR Document Verification** — Tesseract.js (Thai + English) with image quality analysis
- **Approval Queue** — Pending / Approve / Reject workflow for Operations and Compliance teams
- **Customer Database** — 8 seeded customer records, persisted in localStorage
- **Audit Log** — Before/after change log with CSV export
- **CEO Executive Dashboard** — Real-time KPIs, charts, intent breakdown, auto-refresh every 30s

## Project Structure

```
POC-Kiro/
├── Case_Update_Name/
│   ├── index.html          # Main call center UI
│   ├── dashboard.html      # CEO executive dashboard
│   ├── app.js              # Main application logic
│   ├── db.js               # localStorage database layer
│   ├── ocr.js              # Tesseract.js OCR + image analysis engine
│   ├── dashboard.js        # Dashboard data & chart rendering
│   ├── styles.css          # Call center UI styles
│   └── dashboard.css       # Dashboard styles
├── requirements.md         # Original requirements document
└── .aidlc/                 # AI-DLC workflow specs & design documents
    └── specs/sf-case-intent-processor/
        ├── context.md
        ├── design.md
        └── design/
            ├── components.md
            ├── data-model.md
            ├── integration.md
            ├── implementation.md
            └── nfr.md
```

## How to Run

No build step required. Open directly in a browser:

```
Case_Update_Name/index.html      — Call center agent UI
Case_Update_Name/dashboard.html  — CEO executive dashboard
```

> **Note:** OCR verification requires an internet connection on first use to download the Tesseract.js Thai language pack (~30MB from CDN). Subsequent runs use the cached worker. Use **Skip Verification** if offline.

## Tech Stack

| Layer | Technology |
|---|---|
| UI | HTML5 / CSS3 / Vanilla JavaScript |
| OCR | [Tesseract.js v5](https://github.com/naptha/tesseract.js) (Thai + English) |
| Charts | [Chart.js v4](https://www.chartjs.org/) |
| Storage | Browser localStorage (no backend required) |
| Image Analysis | Canvas API (aspect ratio, brightness, edge density) |

## Approval Routing

| Intent | Routing | Reason |
|---|---|---|
| Change Title | ✅ Auto-Approve | Low risk |
| Change Date of Birth | ✅ Auto-Approve | Minor correction |
| Change First Name | 📋 Operations Team | Legal name change |
| Change Last Name | 📋 Operations Team | Legal name change |
| Change Full Name | 📋 Operations Team | Legal name change |
| Change National ID | 🔒 Compliance Team | Sensitive identity data |

## License

MIT
