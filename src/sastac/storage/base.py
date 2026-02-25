"""
Generic SQLite storage engine.

Provides CRUD utilities and safe transactional operations.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional


class SQLiteStorage:
    """
    Lightweight SQLite wrapper.

    Why:
        Centralizes DB access logic and enforces consistent behavior.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.db_path)
        self._connection.row_factory = sqlite3.Row

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def execute(self, query: str, params: Optional[Iterable[Any]] = None) -> None:
        with self._connection:
            self._connection.execute(query, params or [])

    def executemany(
        self, query: str, param_list: Iterable[Iterable[Any]]
    ) -> None:
        with self._connection:
            self._connection.executemany(query, param_list)

    def fetch_one(
        self, query: str, params: Optional[Iterable[Any]] = None
    ) -> Optional[dict[str, Any]]:
        cursor = self._connection.execute(query, params or [])
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetch_all(
        self, query: str, params: Optional[Iterable[Any]] = None
    ) -> list[dict[str, Any]]:
        cursor = self._connection.execute(query, params or [])
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def insert(self, query: str, params: Iterable[Any]) -> int:
        with self._connection:
            cursor = self._connection.execute(query, params)
            return cursor.lastrowid

    def close(self) -> None:
        self._connection.close()
    