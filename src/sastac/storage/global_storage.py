"""
Global storage facade.

Manages ~/.sastac/global.db and workspace registry.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from .base import SQLiteStorage


def get_sastac_home() -> Path:
    return Path.home() / ".sastac"


def get_global_db_path() -> Path:
    return get_sastac_home() / "global.db"


class GlobalStorage:
    """
    Facade over global DB.

    Why:
        Separates global registry concerns from workspace data.
    """

    def __init__(self) -> None:
        self.storage = SQLiteStorage(get_global_db_path())
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        self.storage.execute(
            """
            CREATE TABLE IF NOT EXISTS workspaces (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                root_path TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );
            """
        )

    def create_workspace(self, name: str, root_path: str) -> str:
        workspace_id = str(uuid.uuid4())
        self.storage.execute(
            """
            INSERT INTO workspaces (id, name, root_path, created_at)
            VALUES (?, ?, ?, ?);
            """,
            (
                workspace_id,
                name,
                root_path,
                datetime.utcnow().isoformat(),
            ),
        )
        return workspace_id

    def get_workspace(self, workspace_id: str) -> dict | None:
        return self.storage.fetch_one(
            "SELECT * FROM workspaces WHERE id = ?;",
            (workspace_id,),
        )

    def list_workspaces(self) -> list[dict]:
        return self.storage.fetch_all("SELECT * FROM workspaces;")

    def delete_workspace(self, workspace_id: str) -> None:
        self.storage.execute(
            "DELETE FROM workspaces WHERE id = ?;",
            (workspace_id,),
        )
