from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import List

from sastac.util.service import FileSystemService
from sastac.storage.scopes.workspace_storage import WorkspaceStorage
from sastac.ast.chunk_indexer import ChunkIndexer
from sastac.context.structure_summarizer import StructureSummarizer
from sastac.context.file_indexer import FileIndexer
from sastac.util.logger import logger


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

    def __init__(self, workspace_id: str, base_dir: Path, embed_fn, storage: WorkspaceStorage | None = None):
        self.storage = storage or WorkspaceStorage(workspace_id, base_dir)
        self.chunk_indexer = ChunkIndexer(self.storage, embed_fn)
        self.structure_summarizer = StructureSummarizer(self.storage)

    # ------------------------------------
    # Step 1: File metadata → SQLite
    # ------------------------------------

    def index_files(self, root: Path) -> tuple[List[Path], List[Path]]:

        files = FileSystemService.get_workspace_files(
            path=root,
            prefix=''
        )

        indexed = []
        modified = []

        for f in files:

            if len(indexed) >= MAX_FILES:
                logger.info(f"Reached max files ({MAX_FILES})")
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
            modified.append(f)

        logger.info(f"Indexed metadata for {len(indexed)} files, {len(modified)} modified")
        return indexed, modified


    # ------------------------------------
    # Step 2: Code chunks → Qdrant
    # ------------------------------------

    def index_chunks(self, files: List[Path]) -> List[str]:

        logger.info("Chunk indexing started")
        return self.chunk_indexer.index(files)


    # ------------------------------------
    # Full pipeline
    # ------------------------------------

    def build(self, root: Path):

        logger.info(f"Indexing workspace at {root}")

        all_files, modified_files = self.index_files(root)
        if modified_files:
            logger.info(f"Re-indexing {len(modified_files)} modified files")
            chunk_ids = self.index_chunks(modified_files)
            logger.info(f"Finished indexing {len(chunk_ids)} chunks for {len(modified_files)} modified files")
            # Summarize directories of modified files
            modified_dirs = {f.parent for f in modified_files}
            for d in modified_dirs:
                # Find all logical files in this dir to provide context
                dir_files = [f for f in all_files if f.parent == d]
                self.structure_summarizer.summarize_directory(d, dir_files)
            logger.info(f"Summarized {len(modified_dirs)} directories")
        else:
            logger.info("No files modified; skipping chunk indexing")

        logger.info("Workspace indexing complete")
        return all_files
