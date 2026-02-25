import os
import sqlite3
import time
from pathlib import Path
from typing import Iterator, Tuple

DB_PATH = "project_files.db"


# -----------------------------
# Language inference
# -----------------------------
EXTENSION_LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".md": "markdown",
    ".sh": "shell",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".sql": "sql",
}


def infer_language(path: Path) -> str:
    return EXTENSION_LANGUAGE_MAP.get(path.suffix.lower(), "unknown")


# -----------------------------
# DB Setup
# -----------------------------
def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def initialize_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS files (
            project_id TEXT NOT NULL,
            path TEXT NOT NULL,
            language TEXT,
            size INTEGER NOT NULL,
            last_modified INTEGER NOT NULL,
            PRIMARY KEY (project_id, path)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_files_project
        ON files (project_id)
    """)
    conn.commit()


# -----------------------------
# File scanning
# -----------------------------
def scan_project(
    project_id: str,
    root_path: str
) -> Iterator[Tuple[str, str, str, int, int]]:
    """
    Yields:
        (project_id, relative_path, language, size, last_modified)
    """
    root = Path(root_path)

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue

        rel_path = file_path.relative_to(root).as_posix()
        stat = file_path.stat()

        yield (
            project_id,
            rel_path,
            infer_language(file_path),
            stat.st_size,
            int(stat.st_mtime),
        )


# -----------------------------
# Rebuild project index
# -----------------------------
def rebuild_project(
    conn: sqlite3.Connection,
    project_id: str,
    root_path: str
) -> None:
    """
    Deletes all rows for project and rebuilds from filesystem.
    """
    with conn:
        conn.execute("DELETE FROM files WHERE project_id = ?", (project_id,))
        conn.executemany("""
            INSERT INTO files (project_id, path, language, size, last_modified)
            VALUES (?, ?, ?, ?, ?)
        """, scan_project(project_id, root_path))


# -----------------------------
# Optional: incremental upsert
# -----------------------------
def upsert_files(
    conn: sqlite3.Connection,
    rows: Iterator[Tuple[str, str, str, int, int]]
) -> None:
    """
    Uses SQLite UPSERT (requires SQLite >= 3.24).
    """
    with conn:
        conn.executemany("""
            INSERT INTO files (project_id, path, language, size, last_modified)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(project_id, path)
            DO UPDATE SET
                language=excluded.language,
                size=excluded.size,
                last_modified=excluded.last_modified
        """, rows)


def clean_project(conn: sqlite3.Connection, project_id: str) -> None:
    with conn:
        conn.execute("DELETE FROM files WHERE project_id = ?", (project_id,))


def get_project_files(conn: sqlite3.Connection, project_id: str):
    conn.row_factory = sqlite3.Row

    cursor = conn.execute("""
        SELECT *
        FROM files
        WHERE project_id = ?
        ORDER BY path
    """, (project_id,))

    for row in cursor:
        yield dict(row)


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    PROJECT_ID = "stocks"
    ROOT_PATH = "/home/adarsh/code/booklore"

    conn = get_connection()
    initialize_db(conn)

    rebuild_project(conn, PROJECT_ID, ROOT_PATH)

    print("Project indexed successfully.")
    for entry in get_project_files(conn, project_id="stocks"):
        print(entry)
