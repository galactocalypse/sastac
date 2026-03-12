from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import List

from sastac.fs.service import FileSystemService
from sastac.storage.scopes.workspace_storage import WorkspaceStorage
from sastac.ast.chunk_indexer import ChunkIndexer


# -------------------------------------------------------
# Config
# -------------------------------------------------------

ALLOWED_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".go", ".java"
}

SKIP_DIRS = {
    ".git", "node_modules", "dist", "build",
    ".venv", "__pycache__", ".idea", ".vscode",
    "vendor", "src/test", "test"
}


MAX_FILE_SIZE = 500_000
MAX_FILES = 20_000


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def detect_language(path: Path) -> str | None:
    ext = path.suffix.lower()
    return {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".go": "go",
        ".java": "java",
    }.get(ext)


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


# -------------------------------------------------------
# Indexer
# -------------------------------------------------------

class WorkspaceIndexer:

    def __init__(self, workspace_id: str, base_dir: Path, embed_fn):
        self.storage = WorkspaceStorage(workspace_id, base_dir)
        self.chunk_indexer = ChunkIndexer(self.storage, embed_fn)

    # ------------------------------------
    # Step 1: File metadata → SQLite
    # ------------------------------------

    def index_files(self, root: Path) -> List[Path]:

        files = FileSystemService.list_files(root=root, recursive=True)

        indexed = []

        for f in files:

            if len(indexed) >= MAX_FILES:
                print(f"Reached max files ({MAX_FILES})")
                break

            if should_skip(f):
                continue

            if f.suffix.lower() not in ALLOWED_EXTENSIONS:
                continue

            if f.stat().st_size > MAX_FILE_SIZE:
                continue

            try:
                h = file_hash(f)
            except Exception:
                continue

            key = f"file:{f}"
            prev = self.storage.kv.get(key)

            if prev and prev.get("hash") == h:
                indexed.append(f)
                continue

            metadata = {
                "path": str(f),
                "hash": h,
                "size": f.stat().st_size,
                "mtime": f.stat().st_mtime,
                "language": detect_language(f),
                "indexed_at": time.time(),
            }

            self.storage.kv.set(key, metadata)
            indexed.append(f)

        print(f"Indexed metadata for {len(indexed)} files")
        return indexed


    # ------------------------------------
    # Step 2: Code chunks → Qdrant
    # ------------------------------------

    def index_chunks(self, files: List[Path]):

        print("Chunk indexing started")
        self.chunk_indexer.index(files)


    # ------------------------------------
    # Full pipeline
    # ------------------------------------

    def build(self, root: Path):

        print(f"Indexing workspace at {root}")

        files = self.index_files(root)
        self.index_chunks(files)

        print("Workspace indexing complete")
