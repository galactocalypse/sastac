from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import List

from sastac.util.service import FileSystemService
from sastac.storage.scopes.workspace_storage import WorkspaceStorage

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".go", ".java"
}

SKIP_DIRS = {
    ".git", "node_modules", "dist", "build",
    "__pycache__", ".venv", ".idea", ".vscode"
}

MAX_FILE_SIZE = 200_000
MAX_FILES = 10_000


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def should_skip(path: Path) -> bool:
    return any(p in SKIP_DIRS for p in path.parts)


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


class FileIndexer:

    def __init__(self, storage: WorkspaceStorage):
        self.storage = storage

    def index(self, root: Path) -> List[Path]:

        files = FileSystemService.list_files(root=root, recursive=True)
        indexed: List[Path] = []

        for f in files:

            if len(indexed) >= MAX_FILES:
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
            if prev and prev["hash"] == h:
                indexed.append(f)
                continue

            self.storage.kv.set(key, {
                "path": str(f),
                "hash": h,
                "size": f.stat().st_size,
                "mtime": f.stat().st_mtime,
                "language": detect_language(f),
                "indexed_at": time.time(),
            })

            indexed.append(f)

        return indexed
