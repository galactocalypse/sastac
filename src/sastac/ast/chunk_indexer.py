from __future__ import annotations

import uuid
from pathlib import Path
from typing import List

from sastac.ast.chunker import extract_code_chunks
from sastac.storage.scopes.workspace_storage import WorkspaceStorage

MAX_CHUNKS_PER_FILE = 500
MAX_CHUNK_SIZE = 20000
MIN_CHUNK_SIZE = 10


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


class ChunkIndexer:

    def __init__(self, storage: WorkspaceStorage, embed_fn):
        self.storage = storage
        self.embed_fn = embed_fn

    def index(self, files: List[Path]):

        ids = []
        vectors = []
        metadata = []

        for f in files:

            lang = detect_language(f)
            if not lang:
                continue

            try:
                source = f.read_text()
                chunks = extract_code_chunks(lang, source)
            except Exception:
                continue

            chunks = chunks[:MAX_CHUNKS_PER_FILE]

            for c in chunks:

                if len(c.body) < MIN_CHUNK_SIZE:
                    print("SKIPPED SMALL:", f, c.signature[:60])
                    continue

                if len(c.body) > MAX_CHUNK_SIZE:
                    print("SKIPPED LARGE:", f, c.signature[:60])
                    continue

                ids.append(uuid.uuid4())
                vectors.append(self.embed_fn(c.body))

                metadata.append({
                    "file": str(f),
                    "name": c.name,
                    "node_type": c.node_type,
                    "class": c.class_name,
                    "package": c.package,
                    "class_annotations": c.class_annotations,
                    "method_annotations": c.method_annotations,
                    "signature": c.signature,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                })

        if ids:
            self.storage.vector.upsert(ids, vectors, metadata)
