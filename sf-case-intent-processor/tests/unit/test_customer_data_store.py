"""Unit tests for CustomerDataStore."""

import json
import pytest
from pathlib import Path
from customer_data_store.store import CustomerDataStore
from shared.exceptions import StorageInitError


SAMPLE_DATA = {
    "C001234": {
        "cid": "C001234",
        "title": "นาย",
        "first_name": "สมชาย",
        "last_name": "ใจดี",
        "national_id": "1100100012345",
    },
    "C002345": {
        "cid": "C002345",
        "title": "นาง",
        "first_name": "สมหญิง",
        "last_name": "รักดี",
        "national_id": "1100200023456",
    },
}


@pytest.fixture
def data_file(tmp_path: Path) -> Path:
    f = tmp_path / "customer_data.json"
    f.write_text(json.dumps(SAMPLE_DATA, ensure_ascii=False, indent=2), encoding="utf-8")
    return f


class TestCustomerDataStoreInit:

    def test_init_success(self, data_file):
        store = CustomerDataStore(str(data_file))
        assert store is not None

    def test_init_file_not_found(self, tmp_path):
        with pytest.raises(StorageInitError, match="not found"):
            CustomerDataStore(str(tmp_path / "nonexistent.json"))

    def test_init_invalid_json(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json {{{", encoding="utf-8")
        with pytest.raises(StorageInitError, match="Invalid JSON"):
            CustomerDataStore(str(bad_file))

    def test_init_json_array_raises(self, tmp_path):
        arr_file = tmp_path / "array.json"
        arr_file.write_text("[]", encoding="utf-8")
        with pytest.raises(StorageInitError, match="must be a JSON object"):
            CustomerDataStore(str(arr_file))


class TestCustomerDataStoreGet:

    def test_get_existing_cid(self, data_file):
        store = CustomerDataStore(str(data_file))
        record = store.get("C001234")
        assert record is not None
        assert record["first_name"] == "สมชาย"
        assert record["last_name"] == "ใจดี"

    def test_get_nonexistent_cid(self, data_file):
        store = CustomerDataStore(str(data_file))
        assert store.get("UNKNOWN") is None


class TestCustomerDataStoreUpdate:

    def test_update_first_name(self, data_file):
        store = CustomerDataStore(str(data_file))
        result = store.update("C001234", "first_name", "ดารุณี")
        assert result.ok is True
        assert result.field_updated == "first_name"
        # Verify persisted
        record = store.get("C001234")
        assert record["first_name"] == "ดารุณี"

    def test_update_last_name(self, data_file):
        store = CustomerDataStore(str(data_file))
        result = store.update("C001234", "last_name", "อะฟาฟ")
        assert result.ok is True
        # Other fields preserved
        record = store.get("C001234")
        assert record["last_name"] == "อะฟาฟ"
        assert record["first_name"] == "สมชาย"  # unchanged
        assert record["title"] == "นาย"  # unchanged

    def test_update_title(self, data_file):
        store = CustomerDataStore(str(data_file))
        result = store.update("C001234", "title", "นาง")
        assert result.ok is True
        record = store.get("C001234")
        assert record["title"] == "นาง"
        assert record["first_name"] == "สมชาย"  # unchanged

    def test_update_preserves_all_other_fields(self, data_file):
        store = CustomerDataStore(str(data_file))
        store.update("C001234", "first_name", "NEW")
        record = store.get("C001234")
        assert record["cid"] == "C001234"
        assert record["title"] == "นาย"
        assert record["last_name"] == "ใจดี"
        assert record["national_id"] == "1100100012345"

    def test_update_cid_not_found(self, data_file):
        store = CustomerDataStore(str(data_file))
        result = store.update("UNKNOWN_CID", "first_name", "test")
        assert result.ok is False
        assert result.reason == "CID_NOT_FOUND"

    def test_update_does_not_affect_other_records(self, data_file):
        store = CustomerDataStore(str(data_file))
        store.update("C001234", "first_name", "CHANGED")
        # Other record unchanged
        other = store.get("C002345")
        assert other["first_name"] == "สมหญิง"

    def test_update_new_field_adds_it(self, data_file):
        store = CustomerDataStore(str(data_file))
        result = store.update("C001234", "email", "new@email.com")
        assert result.ok is True
        record = store.get("C001234")
        assert record["email"] == "new@email.com"
