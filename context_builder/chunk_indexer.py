import uuid
import os
import tiktoken
from pathlib import Path
from typing import List, Dict, Iterator

from tree_sitter import Parser, Language

# Import grammars you need
import tree_sitter_python as python_lang
import tree_sitter_javascript as javascript_lang
import tree_sitter_typescript as language_typescript
import tree_sitter_go as go_lang
import tree_sitter_java as java_lang

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer


# ----------------------------
# Config
# ----------------------------

IGNORED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    ".venv",
    "venv",
}

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".go": "go",
}

LANGUAGE_REGISTRY = {
    "python": python_lang,
    "javascript": javascript_lang,
    "typescript": language_typescript,
    "go": go_lang,
    "java": java_lang,
}

TOP_LEVEL_NODE_TYPES = {
    "python": {"function_definition", "class_definition"},
    "javascript": {"function_declaration", "class_declaration", "method_definition"},
    "typescript": {"function_declaration", "class_declaration", "method_definition"},
    "go": {"function_declaration", "method_declaration"},
    "java": {"class_declaration", "method_declaration"},
}

PARSER_CACHE = {}

MAX_TOKENS = 800
COLLECTION_NAME = "code_chunks"

encoder = tiktoken.get_encoding("cl100k_base")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
qdrant = QdrantClient(host="localhost", port=6333)


# ----------------------------
# Parser loader
# ----------------------------

def get_parser(language: str):
    if language not in LANGUAGE_REGISTRY:
        return None

    if language not in PARSER_CACHE:
        parser = Parser()

        # Convert PyCapsule -> Language
        lang_obj = Language(LANGUAGE_REGISTRY[language].language())
        parser.language = lang_obj

        PARSER_CACHE[language] = parser

    return PARSER_CACHE[language]

# ----------------------------
# Language inference
# ----------------------------

def infer_language(path: Path):
    return SUPPORTED_EXTENSIONS.get(path.suffix.lower())


# ----------------------------
# Recursive file generator
# ----------------------------

def iter_project_files(root: Path) -> Iterator[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        for filename in filenames:
            yield Path(dirpath) / filename


# ----------------------------
# Qdrant Setup
# ----------------------------

def ensure_collection(vector_dim: int):
    if COLLECTION_NAME not in [c.name for c in qdrant.get_collections().collections]:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=vector_dim,
                distance=Distance.COSINE,
            ),
        )


# ----------------------------
# Token limiter
# ----------------------------

def enforce_token_limit(text: str) -> List[str]:
    tokens = encoder.encode(text)
    if len(tokens) <= MAX_TOKENS:
        return [text]

    chunks = []
    start = 0
    while start < len(tokens):
        end = start + MAX_TOKENS
        chunk_tokens = tokens[start:end]
        chunks.append(encoder.decode(chunk_tokens))
        start = end
    return chunks


# ----------------------------
# Tree-sitter chunking
# ----------------------------

def chunk_with_treesitter(code: str, language: str) -> List[Dict]:
    parser = get_parser(language)
    if parser is None:
        return []

    tree = parser.parse(bytes(code, "utf8"))
    root = tree.root_node

    allowed_types = TOP_LEVEL_NODE_TYPES.get(language, set())
    chunks = []

    for node in root.children:
        if node.type in allowed_types:
            chunk_text = code[node.start_byte:node.end_byte]

            chunks.append({
                "text": chunk_text,
                "symbol": node.type,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
            })

    return chunks


# ----------------------------
# Fallback heuristic chunker
# ----------------------------

def heuristic_chunk(code: str) -> List[Dict]:
    lines = code.splitlines()
    chunks = []
    buffer = []
    start_line = 1

    for i, line in enumerate(lines, 1):
        buffer.append(line)
        if line.strip() == "":
            text = "\n".join(buffer).strip()
            if text:
                chunks.append({
                    "text": text,
                    "symbol": "block",
                    "start_line": start_line,
                    "end_line": i,
                })
            buffer = []
            start_line = i + 1

    if buffer:
        chunks.append({
            "text": "\n".join(buffer),
            "symbol": "block",
            "start_line": start_line,
            "end_line": len(lines),
        })

    return chunks


# ----------------------------
# Main chunking logic
# ----------------------------

def chunk_file(path: Path, language: str, project_id: str):
    print(f"Chunking: {path}")
    code = path.read_text(errors="ignore")

    chunks = chunk_with_treesitter(code, language)
    if not chunks:
        chunks = heuristic_chunk(code)

    final_chunks = []

    for chunk in chunks:
        split_texts = enforce_token_limit(chunk["text"])

        for text in split_texts:
            final_chunks.append({
                "id": str(uuid.uuid4()),
                "text": text,
                "metadata": {
                    "project_id": project_id,
                    "path": str(path),
                    "language": language,
                    "symbol": chunk["symbol"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                }
            })

    return final_chunks


# ----------------------------
# Qdrant upsert
# ----------------------------

def upsert_chunks(chunks: List[Dict]):
    texts = [c["text"] for c in chunks]
    embeddings = embedder.encode(texts)

    points = [
        PointStruct(
            id=c["id"],
            vector=embeddings[i],
            payload=c["metadata"],
        )
        for i, c in enumerate(chunks)
    ]

    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )


# ----------------------------
# Search
# ----------------------------

def search(query: str, project_id: str, top_k=5):
    query_vector = embedder.encode(query)

    results = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
        query_filter={
            "must": [
                {
                    "key": "project_id",
                    "match": {"value": project_id}
                }
            ]
        }
    )

    return results


# ----------------------------
# Recursive indexer
# ----------------------------

def index_project(project_id: str, project_root: str, batch_size: int = 64):
    root = Path(project_root)
    buffer: List[Dict] = []

    for path in iter_project_files(root):
        language = infer_language(path)
        if not language:
            continue

        file_chunks = chunk_file(path, language, project_id)

        for chunk in file_chunks:
            buffer.append(chunk)

            if len(buffer) >= batch_size:
                upsert_chunks(buffer)
                buffer.clear()

    if buffer:
        upsert_chunks(buffer)


if __name__ == "__main__":
    ensure_collection(embedder.get_sentence_embedding_dimension())

    index_project(
        project_id="stocks",
        project_root="/home/adarsh/code/booklore"
    )

    results = search(
        "What's the function of AuditService.log?",
        "stocks"
    )

    print(results)