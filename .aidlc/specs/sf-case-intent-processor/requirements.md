# Requirements Document

## Introduction

The SF Case Intent Processor is a system that extracts case data from Salesforce where the case status is not "Closed" **and the intent belongs to the Customer Information Update category**, performs intent-specific validation, and executes the appropriate action. The system focuses exclusively on Customer Information Update intents (e.g., changing first name, title, or last name). When such an intent is identified, the system verifies that a valid document is attached before updating customer data in local storage.

## Glossary

- **SF_Case_Extractor**: The component responsible for querying and retrieving case records from Salesforce
- **Intent_Analyzer**: The component responsible for identifying the intent name from a case and routing it to the appropriate processing logic
- **Document_Validator**: The component responsible for verifying that required documents are attached to a case and checking their validity
- **Customer_Data_Store**: The local storage system where customer data is maintained, keyed by CID (Customer ID)
- **CID**: Customer ID — the unique identifier used as the key for customer records in the Customer_Data_Store
- **Intent**: A categorized label describing the purpose or request type of a Salesforce case (e.g., "ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล")
- **Verification_Document**: A document attached to a case that serves as proof for validating a customer's request
- **Case**: A Salesforce record representing a customer service request

## Requirements

### Requirement 1: Extract Non-Closed Customer Information Update Cases from Salesforce

**User Story:** As a system operator, I want to extract all cases from Salesforce where the status is not "Closed" and the intent belongs to the Customer Information Update category, so that only relevant active cases are processed.

#### Acceptance Criteria

1. WHEN the SF_Case_Extractor is triggered, THE SF_Case_Extractor SHALL query Salesforce for all cases where the status field is not equal to "Closed" AND the intent name field matches the Customer Information Update category (e.g., "ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล"), and return the results within 30 seconds
2. WHEN cases are retrieved from Salesforce, THE SF_Case_Extractor SHALL include at minimum the case ID, CID, intent name, and status fields for each case in the extracted data
3. IF the Salesforce query fails, returns an error, or does not respond within 30 seconds, THEN THE SF_Case_Extractor SHALL retry the query up to 3 times before logging the error details and reporting the failure without processing any cases
4. WHEN no matching cases exist in Salesforce, THE SF_Case_Extractor SHALL return an empty result set and log that zero cases were found
5. THE SF_Case_Extractor SHALL NOT retrieve cases whose intent does not belong to the Customer Information Update category, even if those cases are non-closed

### Requirement 2: Identify Specific Customer Information Update Sub-Intent from Each Case

**User Story:** As a system operator, I want the system to identify the specific sub-intent (first name, title, or last name change) from each extracted case, so that the correct field update is applied.

#### Acceptance Criteria

1. WHEN a case is extracted, THE Intent_Analyzer SHALL extract the intent name from the intent name field of the case record
2. IF a case has a missing, empty, or whitespace-only intent name field, THEN THE Intent_Analyzer SHALL flag the case as unprocessable and log the case ID with the reason indicating the intent name is absent
3. IF a case contains an intent name that does not match any registered Customer Information Update sub-intent processor, THEN THE Intent_Analyzer SHALL flag the case as unprocessable and log the case ID with the unrecognized intent name
4. WHEN a valid intent name is extracted and matches a registered sub-intent processor, THE Intent_Analyzer SHALL route the case to the processing logic registered for that sub-intent

### Requirement 3: Analyze Case by Customer Information Update Sub-Intent

**User Story:** As a system operator, I want the system to analyze each case based on its specific Customer Information Update sub-intent, so that the correct business rules are applied for each field change type.

#### Acceptance Criteria

1. THE Intent_Analyzer SHALL support registration of multiple Customer Information Update sub-intent processors (e.g., first name change, title change, last name change), each with distinct validation and processing rules
2. WHEN a case is routed to a sub-intent processor, THE Intent_Analyzer SHALL execute the validation rules defined for that sub-intent, and upon successful validation, execute the processing actions defined for that sub-intent
3. IF no processing logic is registered for a given sub-intent, THEN THE Intent_Analyzer SHALL log the unhandled intent name and case ID, and skip processing for that case
4. IF validation fails for a routed case, THEN THE Intent_Analyzer SHALL halt processing for that case and log the case ID, intent name, and the validation failure reason

### Requirement 4: Validate Verification Document for Personal Info Change Intent

**User Story:** As a system operator, I want the system to verify that a valid document is attached when the intent is to change first name, title, or last name, so that unauthorized changes are prevented.

#### Acceptance Criteria

1. WHEN the intent matches the personal info change category (e.g., "ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล"), THE Document_Validator SHALL check that at least one Verification_Document is attached to the case
2. IF no Verification_Document is attached to the case, THEN THE Document_Validator SHALL reject the case, log the case ID with an indication that no verification document was found, and halt further processing of that case
3. WHEN at least one Verification_Document is attached, THE Document_Validator SHALL validate that the document status field equals "OK" or "valid" (case-insensitive match against these two accepted values)
4. IF the Verification_Document status does not equal "OK" or "valid," THEN THE Document_Validator SHALL reject the case, log the case ID, document identifier, and current document status value, and halt further processing of that case
5. IF multiple Verification_Documents are attached to the case, THEN THE Document_Validator SHALL consider the case valid only when at least one document has a status of "OK" or "valid"

### Requirement 5: Update Customer Data in Local Storage

**User Story:** As a system operator, I want the system to update customer data in local storage when the verification document is valid, so that approved changes are persisted.

#### Acceptance Criteria

1. WHEN the Document_Validator confirms the Verification_Document is valid, THE Customer_Data_Store SHALL update the customer record using the CID from the case as the lookup key, applying the new field values provided in the case data
2. WHEN updating the customer record, THE Customer_Data_Store SHALL apply only the specific field indicated by the intent (first name, title, or last name) and SHALL preserve all other fields in the customer record unchanged
3. WHEN the customer record is successfully updated, THE Customer_Data_Store SHALL log the update confirmation including the CID and the field that was modified
4. IF the CID from the case does not match any existing record in the Customer_Data_Store, THEN THE Customer_Data_Store SHALL log the error including the unmatched CID and report the case as unprocessed
5. IF the update to the Customer_Data_Store fails due to a system or storage error, THEN THE Customer_Data_Store SHALL log the failure details including the CID and the attempted operation, and report the case as unprocessed

### Requirement 6: Extensible Customer Information Update Sub-Intent Processing

**User Story:** As a developer, I want the system to support adding new Customer Information Update sub-intents with different validation rules, so that the system can handle additional field change types in the future without major refactoring.

#### Acceptance Criteria

1. THE Intent_Analyzer SHALL provide a registration interface that allows adding new Customer Information Update sub-intent processors without modifying existing processing logic, where each processor is associated with a unique intent name
2. WHEN a new sub-intent processor is registered, THE Intent_Analyzer SHALL route cases whose intent name exactly matches the registered intent name to the new processor
3. THE Intent_Analyzer SHALL enforce at registration time that each registered sub-intent processor defines at least one validation rule and at least one processing action, and SHALL reject registration if either is missing
4. IF a processor is registered for an intent name that already has a registered processor, THEN THE Intent_Analyzer SHALL reject the duplicate registration and log the conflict including the intent name
