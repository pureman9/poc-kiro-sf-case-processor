---
inclusion: always
---

# Product Context

## Summary
- **Product**: SF Case Intent Processor — automated pipeline that extracts Salesforce cases, identifies intent, validates documents, and updates customer records
- **Users**: System operators, developers
- **Type**: Greenfield — New standalone system

## Overview

The SF Case Intent Processor is an automated data processing system that queries Salesforce for all non-closed cases, identifies the business intent of each case, applies intent-specific validation rules, and performs the appropriate action (such as updating customer data in local storage). The system is designed to be extensible — new intents can be registered without modifying existing logic.

## Problem Statement

Customer service cases in Salesforce require manual processing to identify what action needs to be taken and to validate that required documents are present before making changes to customer records. This system automates that pipeline, reducing manual effort and ensuring consistent validation rules are applied for each intent type.

## Target Users

- **System Operator**: Runs and monitors the pipeline; needs reliable execution, clear error logs, and audit trails for every case processed or skipped
- **Developer**: Extends the system with new intent processors; needs a clean registration interface that doesn't require modifying existing code

## Key Features

- **Case Extraction**: Query Salesforce for all non-closed cases with retry logic and timeout handling
- **Intent Routing**: Identify and route cases to registered intent processors based on intent name
- **Document Validation**: Verify that required verification documents are attached and have valid status for personal info change intents
- **Customer Data Update**: Update specific fields (first name, title, last name) in local storage using CID as the lookup key
- **Extensible Intent Registry**: Register new intent processors without modifying existing logic

## Domain Language

| Term | Definition | Example |
|------|-----------|---------|
| SF_Case_Extractor | Component that queries and retrieves case records from Salesforce | Queries all cases where status != "Closed" |
| Intent_Analyzer | Component that identifies intent name and routes to the correct processor | Routes "ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล" to personal info change processor |
| Document_Validator | Component that verifies required documents are attached and valid | Checks document status == "OK" or "valid" |
| Customer_Data_Store | Local storage system for customer records, keyed by CID | Updates first name field for CID "C001234" |
| CID | Customer ID — unique identifier for customer records | "C001234" |
| Intent | Categorized label describing the purpose of a Salesforce case | "ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล" |
| Verification_Document | Document attached to a case as proof for validating a request | ID card scan with status "OK" |
| Case | Salesforce record representing a customer service request | Case with ID, CID, intent name, status fields |

## Success Criteria

- All non-closed Salesforce cases are extracted and processed within 30 seconds of trigger
- Cases with invalid or missing documents are rejected and logged — no unauthorized data changes
- New intent processors can be registered without modifying existing code
- Every processed, skipped, or failed case has a log entry with sufficient detail for audit

## Constraints & Assumptions

**Constraints**:
- Salesforce query must complete within 30 seconds; retry up to 3 times on failure
- Document validation must accept "OK" or "valid" (case-insensitive) as valid statuses
- Customer data updates must only modify the specific field indicated by the intent — all other fields preserved
- Duplicate intent registrations must be rejected at registration time

**Assumptions**:
- Salesforce API is accessible from the deployment environment
- CID values in Salesforce cases match CID keys in the Customer_Data_Store
- Intent names are exact string matches (no fuzzy matching)
- The system is triggered on-demand or on a schedule (not event-driven from Salesforce)

## Project Type

- **Type**: Greenfield
- **Scope**: New standalone system
