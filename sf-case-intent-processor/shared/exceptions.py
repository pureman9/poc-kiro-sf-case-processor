"""Shared exception classes for the SF Case Intent Processor pipeline."""


class ExtractionError(Exception):
    """Raised when Salesforce case extraction fails after all retries."""
    pass


class StorageInitError(Exception):
    """Raised when the customer data store cannot be initialized (file missing, invalid JSON)."""
    pass


class CIDNotFoundError(Exception):
    """Raised when a CID does not exist in the customer data store."""
    def __init__(self, cid: str):
        self.cid = cid
        super().__init__(f"Customer ID not found: {cid}")


class RegistrationError(Exception):
    """Raised when intent processor registration fails (duplicate or invalid)."""
    pass
