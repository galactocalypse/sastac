# storage/backends/sqlite_kv.py

import sqlite3
import json
from pathlib import Path
from sastac.storage.interfaces.kv_store import KVStore


class SQLiteKVStore(KVStore):

    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS kv (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

    def get(self, key):
        cur = self.conn.execute("SELECT value FROM kv WHERE key=?", (key,))
        row = cur.fetchone()
        return json.loads(row[0]) if row else None

    def set(self, key, value):
        self.conn.execute(
            "INSERT OR REPLACE INTO kv VALUES (?, ?)",
            (key, json.dumps(value)),
        )
        self.conn.commit()

    def delete(self, key):
        self.conn.execute("DELETE FROM kv WHERE key=?", (key,))
        self.conn.commit()

    def list(self, prefix=""):
        cur = self.conn.execute(
            "SELECT key FROM kv WHERE key LIKE ?",
            (prefix + "%",),
        )
        return [r[0] for r in cur.fetchall()]
