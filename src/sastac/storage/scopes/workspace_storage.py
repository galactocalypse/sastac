# storage/scopes/workspace_scope.py

from pathlib import Path
from sastac.storage.backends.sqlite_kv import SQLiteKVStore
from sastac.storage.backends.qdrant_vector import QdrantVectorStore
from sastac.config.loader import load_config


class WorkspaceStorage:

    def __init__(self, workspace_id: str, base_dir: Path):
        root = base_dir / "workspaces" / workspace_id
        root.mkdir(parents=True, exist_ok=True)

        self.kv = SQLiteKVStore(root / "meta.db")
        cfg = load_config()

        self.vector = QdrantVectorStore(
            collection=f"ws_{workspace_id}",
            path=str(root / "qdrant"),
            vector_size=cfg.embeddings.vector_size
        )
