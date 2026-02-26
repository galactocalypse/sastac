# storage/scopes/workspace_scope.py

from pathlib import Path
from sastac.storage.backends.sqlite_kv import SQLiteKVStore
from sastac.storage.backends.qdrant_vector import QdrantVectorStore


class GlobalStorage:

    def __init__(self, base_dir: Path):
        root = base_dir / "common"
        root.mkdir(parents=True, exist_ok=True)

        self.kv = SQLiteKVStore(root / "meta.db")
        self.vector = QdrantVectorStore(
            collection=f"common",
            path=str(root / "qdrant"),
        )
