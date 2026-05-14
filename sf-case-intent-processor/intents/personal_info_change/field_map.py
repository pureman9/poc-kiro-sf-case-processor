"""Intent name → field mapping for Customer Information Update.

Scope: CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล only.

Real Salesforce field mapping (from Case #00001659):
    Process_Add_Info_1__c = new first name (ชื่อใหม่)
    Process_Add_Info_2__c = new last name (นามสกุลใหม่)
    Process_Add_Info_3__c = new title/prefix (คำนำหน้าใหม่)
    Process_Add_Info_4__c = old name (ชื่อเดิม)
    Process_Add_Info_9__c = citizen ID (เลขบัตรประชาชน)
"""

# The single intent type we handle
INTENT_TYPE = "CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล"

# Field mapping for this intent
INTENT_FIELD_MAP: dict[str, dict] = {
    INTENT_TYPE: {
        "label_th": "เปลี่ยนแปลงชื่อ-นามสกุล",
        "label_en": "Change Name (First + Last)",
        "source_fields": ["new_first_name", "new_last_name"],   # SFCase attributes
        "target_fields": ["first_name", "last_name"],           # customer_data_store fields
        "approval_level": "OPS",
        "required_doc": "Thai National ID Card (บัตรประชาชน)",
    },
}

# All supported intent type strings (for registration)
SUPPORTED_INTENTS: list[str] = list(INTENT_FIELD_MAP.keys())
