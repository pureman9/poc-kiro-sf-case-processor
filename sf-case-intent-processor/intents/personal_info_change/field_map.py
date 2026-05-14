"""Intent name → field mapping for Customer Information Update.

Extensible: เพิ่ม intent ใหม่ได้โดยเพิ่ม entry ใน INTENT_FIELD_MAP
SOQL query จะ filter ตาม SUPPORTED_INTENTS อัตโนมัติ

Real Salesforce field mapping (from sandbox):
    Process_Add_Info_1__c = new first name (ชื่อใหม่)
    Process_Add_Info_2__c = new last name (นามสกุลใหม่)
    Process_Add_Info_3__c = new title/prefix (คำนำหน้าใหม่)
    Process_Add_Info_4__c = old name (ชื่อเดิม)
    Process_Add_Info_9__c = citizen ID (เลขบัตรประชาชน)
"""

# ═══════════════════════════════════════════════════════════════════════════════
# INTENT REGISTRY — เพิ่ม intent ใหม่ที่นี่
# Key = Type__c value จาก Salesforce (exact match)
# ═══════════════════════════════════════════════════════════════════════════════

INTENT_FIELD_MAP: dict[str, dict] = {

    # ── ข้อมูลส่วนตัว (Personal Info) ──────────────────────────────────────────

    "CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล": {
        "label_th": "เปลี่ยนแปลงชื่อ-นามสกุล",
        "label_en": "Change Name (First + Last)",
        "source_fields": ["new_first_name", "new_last_name"],
        "target_fields": ["first_name", "last_name"],
        "approval_level": "OPS",
        "required_doc": "Thai National ID Card (บัตรประชาชน)",
    },

    "CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ": {
        "label_th": "เปลี่ยนแปลงชื่อ",
        "label_en": "Change First Name",
        "source_fields": ["new_first_name"],
        "target_fields": ["first_name"],
        "approval_level": "OPS",
        "required_doc": "Thai National ID Card (บัตรประชาชน)",
    },

    "CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงนามสกุล": {
        "label_th": "เปลี่ยนแปลงนามสกุล",
        "label_en": "Change Last Name",
        "source_fields": ["new_last_name"],
        "target_fields": ["last_name"],
        "approval_level": "OPS",
        "required_doc": "Thai National ID Card (บัตรประชาชน)",
    },

    "CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงคำนำหน้า": {
        "label_th": "เปลี่ยนแปลงคำนำหน้า",
        "label_en": "Change Title / Prefix",
        "source_fields": ["new_title"],
        "target_fields": ["title"],
        "approval_level": "AUTO",
        "required_doc": "Thai National ID Card (บัตรประชาชน)",
    },

    # ── ที่อยู่ / เบอร์โทร / อีเมล ────────────────────────────────────────────

    "CC - ข้อมูลส่วนตัว - ที่อยู่": {
        "label_th": "เปลี่ยนแปลงที่อยู่",
        "label_en": "Change Address",
        "source_fields": ["new_first_name"],  # Process_Add_Info_1__c = new address
        "target_fields": ["address"],
        "approval_level": "AUTO",
        "required_doc": "สำเนาทะเบียนบ้าน / หลักฐานที่อยู่ใหม่",
    },

    "CC - ข้อมูลส่วนตัว - หมายเลขโทรศัพท์ในการติดต่อ": {
        "label_th": "เปลี่ยนแปลงเบอร์โทร",
        "label_en": "Change Phone Number",
        "source_fields": ["new_first_name"],  # Process_Add_Info_1__c = new phone
        "target_fields": ["phone"],
        "approval_level": "AUTO",
        "required_doc": "ไม่ต้องใช้เอกสาร (ยืนยันตัวตนผ่าน OTP)",
    },

    "CC - ข้อมูลส่วนตัว - อีเมล": {
        "label_th": "เปลี่ยนแปลงอีเมล",
        "label_en": "Change Email",
        "source_fields": ["new_first_name"],  # Process_Add_Info_1__c = new email
        "target_fields": ["email"],
        "approval_level": "AUTO",
        "required_doc": "ไม่ต้องใช้เอกสาร (ยืนยันตัวตนผ่าน OTP)",
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # เพิ่ม intent ใหม่ด้านล่างนี้ — format เดียวกัน
    # ═══════════════════════════════════════════════════════════════════════════
}

# All supported intent type strings (auto-generated from map keys)
SUPPORTED_INTENTS: list[str] = list(INTENT_FIELD_MAP.keys())


def get_intent_config(intent_type: str) -> dict | None:
    """Look up intent configuration by Type__c value.

    Args:
        intent_type: Exact Type__c value from Salesforce.

    Returns:
        Intent config dict or None if not registered.
    """
    return INTENT_FIELD_MAP.get(intent_type)


def get_all_intent_type_prefixes() -> list[str]:
    """Get unique Type__c prefixes for SOQL query filtering.

    Returns list of prefixes that cover all registered intents.
    Used by soql_builder to construct WHERE clause.
    """
    prefixes = set()
    for intent_type in SUPPORTED_INTENTS:
        # Extract prefix before the last " : " separator
        # e.g., "CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล" → "CC - ข้อมูลส่วนตัว"
        parts = intent_type.split(" : ")
        if len(parts) >= 2:
            prefixes.add(parts[0])
        else:
            prefixes.add(intent_type)
    return sorted(prefixes)
