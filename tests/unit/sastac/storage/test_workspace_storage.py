"""
Unit tests for WorkspaceStorage.
"""

from pathlib import Path

import pytest

from sastac.storage.workspace_storage import WorkspaceStorage


class TestWorkspaceStorage:
    @pytest.fixture(autouse=True)
    def isolate_home(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("HOME", str(tmp_path))

    def test_upsert_file(self) -> None:
        storage = WorkspaceStorage("ws1")

        storage.upsert_file("file.py", "hash1")

        file_row = storage.get_file("file.py")
        assert file_row is not None
        assert file_row["hash"] == "hash1"

        storage.upsert_file("file.py", "hash2")

        updated_row = storage.get_file("file.py")
        assert updated_row["hash"] == "hash2"

    def test_add_and_query_symbols(self) -> None:
        storage = WorkspaceStorage("ws2")

        storage.add_symbol(
            name="MyClass",
            kind="class",
            file_path="file.py",
            line=1,
            column=0,
        )

        symbols = storage.get_symbols_by_name("MyClass")

        assert len(symbols) == 1
        assert symbols[0]["kind"] == "class"

    def test_clear_symbols_for_file(self) -> None:
        storage = WorkspaceStorage("ws3")

        storage.add_symbol(
            "func1",
            "function",
            "file.py",
            1,
            0,
        )

        storage.add_symbol(
            "func2",
            "function",
            "file.py",
            2,
            0,
        )

        storage.clear_symbols_for_file("file.py")

        symbols = storage.get_symbols_by_name("func1")
        assert len(symbols) == 0
