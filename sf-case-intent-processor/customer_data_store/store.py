"""CustomerDataStore — read and update customer records in local JSON storage."""

import json
import logging
from pathlib import Path
from filelock import FileLock

from shared.exceptions import StorageInitError, CIDNotFoundError
from customer_data_store.models import UpdateResult

logger = logging.getLogger(__name__)

LOCK_TIMEOUT_SECONDS = 10


class CustomerDataStore:
    """Manages customer records in a local JSON file, keyed by CID.

    Atomic read-modify-write with file locking to prevent corruption.
    Only the specified field is updated — all other fields are preserved.
    """

    def __init__(self, data_path: str):
        """Initialize the store.

        Args:
            data_path: Path to the customer_data.json file.

        Raises:
            StorageInitError: If file doesn't exist or contains invalid JSON.
        """
        self._path = Path(data_path)
        self._lock = FileLock(str(self._path) + ".lock", timeout=LOCK_TIMEOUT_SECONDS)

        # Validate file exists and is valid JSON on init
        if not self._path.exists():
            raise StorageInitError(f"Customer data file not found: {self._path}")

        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise StorageInitError(f"Customer data must be a JSON object, got {type(data).__name__}")
        except json.JSONDecodeError as e:
            raise StorageInitError(f"Invalid JSON in {self._path}: {e}")

    def get(self, cid: str) -> dict | None:
        """Look up a customer record by CID.

        Returns:
            The customer record dict, or None if not found.
        """
        data = self._load()
        return data.get(cid)

    def update(self, cid: str, field: str, value: str) -> UpdateResult:
        """Update a single field for a customer record.

        Only the specified field is modified — all other fields are preserved.
        Uses file locking for atomic read-modify-write.

        Args:
            cid: Customer ID (must exist in store).
            field: Field name to update (e.g., "first_name", "last_name").
            value: New value for the field.

        Returns:
            UpdateResult with ok=True on success, ok=False on failure.
        """
        try:
            with self._lock:
                data = self._load()

                if cid not in data:
                    logger.error(
                        f"CID not found: {cid}",
                        extra={"cid": cid}
                    )
                    return UpdateResult(ok=False, reason="CID_NOT_FOUND", cid=cid)

                # Update only the specified field
                old_value = data[cid].get(field)
                data[cid][field] = value

                # Write back
                self._save(data)

                logger.info(
                    f"Updated {field} for CID {cid}",
                    extra={"cid": cid, "field": field}
                )
                return UpdateResult(ok=True, cid=cid, field_updated=field)

        except Exception as e:
            logger.error(
                f"Storage error for CID {cid}: {e}",
                extra={"cid": cid}
            )
            return UpdateResult(ok=False, reason="STORAGE_ERROR", cid=cid)

    def _load(self) -> dict:
        """Load customer data from JSON file."""
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _save(self, data: dict) -> None:
        """Save customer data to JSON file."""
        self._path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
