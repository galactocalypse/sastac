import pytest
from pathlib import Path

from sastac.storage.backends.sqlite_kv import SQLiteKVStore


@pytest.fixture
def kv_store(tmp_path: Path):
    db_path = tmp_path / "test.db"
    store = SQLiteKVStore(db_path)
    yield store
    store.conn.close()


def test_set_and_get(kv_store):
    kv_store.set("foo", {"a": 1, "b": 2})
    result = kv_store.get("foo")

    assert result == {"a": 1, "b": 2}


def test_get_nonexistent_key_returns_none(kv_store):
    assert kv_store.get("does_not_exist") is None


def test_overwrite_existing_key(kv_store):
    kv_store.set("key", {"v": 1})
    kv_store.set("key", {"v": 2})

    assert kv_store.get("key") == {"v": 2}


def test_delete_key(kv_store):
    kv_store.set("key", {"v": 123})
    kv_store.delete("key")

    assert kv_store.get("key") is None


def test_list_keys_with_prefix(kv_store):
    kv_store.set("proj:1", {"x": 1})
    kv_store.set("proj:2", {"x": 2})
    kv_store.set("user:1", {"x": 3})

    keys = kv_store.list(prefix="proj:")

    assert set(keys) == {"proj:1", "proj:2"}


def test_list_all_keys_when_no_prefix(kv_store):
    kv_store.set("a", 1)
    kv_store.set("b", 2)

    keys = kv_store.list()

    assert set(keys) == {"a", "b"}
