from __future__ import annotations

import uuid
from pathlib import Path
from typing import List

from sastac.ast.chunker import extract_code_chunks


MAX_CHUNKS_PER_FILE = 500
MAX_CHUNK_SIZE = 2000
MIN_CHUNK_SIZE = 10
OVERLAP_RATIO = 0.10  # 10% overlap


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

    def __init__(self, embed_fn):
        self.embed_fn = embed_fn

    def _split_large_chunk(self, chunk):
        """
        Splits a large code chunk into smaller overlapping chunks.
        Returns list of (body, part_index).
        """
        body = chunk.body
        length = len(body)

        if length <= MAX_CHUNK_SIZE:
            return [(body, 0)]

        overlap = int(MAX_CHUNK_SIZE * OVERLAP_RATIO)
        step = MAX_CHUNK_SIZE - overlap

        parts = []
        start = 0
        part_index = 0

        while start < length:
            end = min(start + MAX_CHUNK_SIZE, length)
            sub_body = body[start:end]

            if len(sub_body) >= MIN_CHUNK_SIZE:
                parts.append((sub_body, part_index))

            start += step
            part_index += 1

        return parts

    def index(self, files: List[Path]):

        ids = []
        vectors = []
        metadata = []
        total_chunks = 0
        skipped_small = 0

        for f in files:

            lang = detect_language(f)
            if not lang:
                continue

            try:
                source = f.read_text()
                chunks = extract_code_chunks(lang, source)
                print(f"Extracted {len(chunks)} chunks from {str(f)}")
            except Exception:
                continue

            chunks = chunks[:MAX_CHUNKS_PER_FILE]
            total_chunks += len(chunks)
            chunks_in_file = 0

            for c in chunks:

                if len(c.body) < MIN_CHUNK_SIZE:
                    print("SKIPPED SMALL:", f, c.signature[:60])
                    skipped_small += 1
                    continue

                # Split if large
                sub_chunks = self._split_large_chunk(c)
                chunks_in_file += len(sub_chunks)

                for sub_body, part_index in sub_chunks:

                    ids.append(uuid.uuid4())
                    text = f"""
                    Language: {lang}
                    Package: {c.package}
                    Node type: {c.node_type}
                    Class: {c.class_name}
                    Class annotations: {c.class_annotations}
                    Method annotations: {c.method_annotations}
                    Signature: {c.signature}
                    Docstring: {c.docstring}

                    Code:
                    {sub_body}
                    """

                    vectors.append(self.embed_fn(text))

                    metadata.append({
                        "file": str(f),
                        "name": c.name,
                        "node_type": c.node_type,
                        "class": c.class_name, 
                        "docstring": c.docstring,
                        "package": c.package,
                        "class_annotations": c.class_annotations,
                        "method_annotations": c.method_annotations,
                        "signature": c.signature,
                        "start_line": c.start_line,
                        "end_line": c.end_line,
                        "chunk_part": part_index,
                    })
            print(f"File: {str(f)} - {chunks_in_file} chunks")
        

        print(f"Total extracted chunks: {total_chunks}")
        print(f"Skipped small chunks: {skipped_small}")
        return ids, vectors, metadata
