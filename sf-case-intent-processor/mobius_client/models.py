"""Models for Mobius API client."""

# Title code mapping: Thai title → Mobius titleCode
TITLE_CODE_MAP = {
    "นาย": "MR.",
    "นาง": "MRS.",
    "นางสาว": "MISS",
    "เด็กชาย": "MAST",
    "เด็กหญิง": "MISS",
}


def thai_title_to_mobius_code(thai_title: str) -> str | None:
    """Convert Thai title to Mobius titleCode.

    Args:
        thai_title: Thai title string (e.g., "นาย", "นาง", "นางสาว")

    Returns:
        Mobius title code (e.g., "MR.", "MRS.", "MISS") or None if not mapped.
    """
    return TITLE_CODE_MAP.get(thai_title.strip())
