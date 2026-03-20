from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional

from sastac.ast.chunker import extract_code_chunks, CodeChunk


# -------------------------------------------------------
# Constants
# -------------------------------------------------------

MIN_CHUNK_SIZE: int = 50    # bytes – chunks smaller than this are kept as-is (no filtering)
MAX_CHUNK_SIZE: int = 8_000  # bytes – chunks larger than this are skipped


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

def detect_language(path: Path) -> Optional[str]:
    """Map a file extension to a language identifier."""
    ext = path.suffix.lower()
    return {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".go": "go",
        ".java": "java",
    }.get(ext)


# -------------------------------------------------------
# ChunkIndexer
# -------------------------------------------------------

class ChunkIndexer:
    """
    Indexes source files by extracting AST code chunks, embedding them,
    and upserting into a vector store via ``workspace_storage``.

    Parameters
    ----------
    storage:
        An object with a ``.vector`` attribute that has an
        ``upsert(ids, vectors, metadata)`` method.
    embed_fn:
        A callable ``(text: str) -> list[float]`` that returns an embedding.
    """

    def __init__(self, storage, embed_fn: Callable[[str], List[float]]):
        self.storage = storage
        self.embed_fn = embed_fn

    # --------------------------------------------------
    # Public
    # --------------------------------------------------

    def index(self, files: List[Path]) -> List[str]:
        """
        Process each file, extract chunks, embed, and store.
        """
        ids: List[str] = []
        vectors: List[List[float]] = []
        metadata: List[dict] = []

        for path in files:
            language = detect_language(path)
            if language is None:
                continue

            try:
                source = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            chunks = extract_code_chunks(language, source)

            for chunk in chunks:
                chunk_id = f"{path}:{chunk.start_line}:{chunk.end_line}:{chunk.name}"
                text = chunk.body

                vector = self.embed_fn(text)

                ids.append(chunk_id)
                vectors.append(vector)
                
                meta = chunk.to_metadata()
                meta["path"] = str(path)
                meta["body"] = text
                metadata.append(meta)

        if ids:
            self.storage.vector.upsert(ids, vectors, metadata)
        return ids
