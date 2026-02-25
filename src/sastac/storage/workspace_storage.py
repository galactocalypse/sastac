"""
Workspace-specific storage facade.

Each workspace has its own DB:
~/.sastac/workspaces/<workspace_id>/workspace.db
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime

from .base import SQLiteStorage
from .global_storage import get_sastac_home


class WorkspaceStorage:
    """
    Facade for workspace-scoped data.

    Why:
        Keeps workspace data isolated and portable.
    """

    def __init__(self, workspace_id: str) -> None:
        self.workspace_id = workspace_id
        self.db_path = (
            get_sastac_home()
            / "workspaces"
            / workspace_id
            / "workspace.db"
        )
        self.storage = SQLiteStorage(self.db_path)
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        self.storage.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                hash TEXT NOT NULL,
                last_indexed_at TEXT NOT NULL
            );
            """
        )

        self.storage.execute(
            """
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                kind TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line INTEGER,
                column INTEGER
            );
            """
        )

    # ------------------------
    # File operations
    # ------------------------

    def upsert_file(self, path: str, file_hash: str) -> None:
        now = datetime.utcnow().isoformat()
        self.storage.execute(
            """
            INSERT INTO files (path, hash, last_indexed_at)
            VALUES (?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                hash=excluded.hash,
                last_indexed_at=excluded.last_indexed_at;
            """,
            (path, file_hash, now),
        )

    def get_file(self, path: str) -> dict | None:
        return self.storage.fetch_one(
            "SELECT * FROM files WHERE path = ?;",
            (path,),
        )

    # ------------------------
    # Symbol operations
    # ------------------------

    def add_symbol(
        self,
        name: str,
        kind: str,
        file_path: str,
        line: int,
        column: int,
    ) -> None:
        self.storage.execute(
            """
            INSERT INTO symbols (name, kind, file_path, line, column)
            VALUES (?, ?, ?, ?, ?);
            """,
            (name, kind, file_path, line, column),
        )

    def get_symbols_by_name(self, name: str) -> list[dict]:
        return self.storage.fetch_all(
            "SELECT * FROM symbols WHERE name = ?;",
            (name,),
        )

    def clear_symbols_for_file(self, file_path: str) -> None:
        self.storage.execute(
            "DELETE FROM symbols WHERE file_path = ?;",
            (file_path,),
        )
