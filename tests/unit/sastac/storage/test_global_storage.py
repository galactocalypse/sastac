"""
Unit tests for GlobalStorage.
"""

from pathlib import Path

import pytest

from sastac.storage.global_storage import GlobalStorage


class TestGlobalStorage:
    @pytest.fixture(autouse=True)
    def isolate_home(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("HOME", str(tmp_path))

    def test_create_workspace(self) -> None:
        storage = GlobalStorage()

        workspace_id = storage.create_workspace(
            name="proj",
            root_path="/tmp/proj",
        )

        assert workspace_id is not None

        workspace = storage.get_workspace(workspace_id)
        assert workspace is not None
        assert workspace["name"] == "proj"

    def test_list_workspaces(self) -> None:
        storage = GlobalStorage()

        storage.create_workspace("a", "/a")
        storage.create_workspace("b", "/b")

        workspaces = storage.list_workspaces()
        assert len(workspaces) == 2

    def test_delete_workspace(self) -> None:
        storage = GlobalStorage()

        workspace_id = storage.create_workspace(
            "delete_me",
            "/delete",
        )

        storage.delete_workspace(workspace_id)

        workspace = storage.get_workspace(workspace_id)
        assert workspace is None
