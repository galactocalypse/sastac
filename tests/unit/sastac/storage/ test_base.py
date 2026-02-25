"""
Unit tests for SQLiteStorage.
"""

from pathlib import Path

import pytest

from sastac.storage.base import SQLiteStorage


class TestSQLiteStorage:
    def test_create_and_insert_and_fetch(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        storage = SQLiteStorage(db_path)

        storage.execute(
            """
            CREATE TABLE test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
            """
        )

        storage.insert(
            "INSERT INTO test (name) VALUES (?);",
            ("adarsh",),
        )

        row = storage.fetch_one(
            "SELECT * FROM test WHERE name = ?;",
            ("adarsh",),
        )

        assert row is not None
        assert row["name"] == "adarsh"

    def test_fetch_all(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        storage = SQLiteStorage(db_path)

        storage.execute(
            "CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT);"
        )

        storage.executemany(
            "INSERT INTO test (value) VALUES (?);",
            [("a",), ("b",), ("c",)],
        )

        rows = storage.fetch_all("SELECT * FROM test;")
        assert len(rows) == 3

    def test_delete(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        storage = SQLiteStorage(db_path)

        storage.execute(
            "CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT);"
        )

        storage.insert(
            "INSERT INTO test (value) VALUES (?);",
            ("x",),
        )

        storage.execute("DELETE FROM test;")

        rows = storage.fetch_all("SELECT * FROM test;")
        assert len(rows) == 0
