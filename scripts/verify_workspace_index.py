import argparse
from pathlib import Path
from collections import Counter

from sentence_transformers import SentenceTransformer
from sastac.storage.scopes.workspace_storage import WorkspaceStorage
from sastac.embedding.embedder import embed


# -------------------------------------------
# Helpers
# -------------------------------------------

def print_header(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# -------------------------------------------
# Metadata Checks
# -------------------------------------------

def check_metadata(storage):

    print_header("FILE METADATA")

    keys = storage.kv.list("file:")
    print(f"Indexed files: {len(keys)}")

    langs = Counter()
    backend = 0
    ui = 0

    for k in keys[:1000]:
        meta = storage.kv.get(k)
        if not meta:
            continue

        langs[meta.get("language")] += 1

        path = meta.get("path", "")
        if "booklore-backend" in path:
            backend += 1
        if "booklore-ui" in path:
            ui += 1

    print("\nLanguages:")
    for lang, count in langs.most_common():
        print(f"  {lang}: {count}")

    print("\nBooklore split:")
    print(f"  backend files: {backend}")
    print(f"  ui files     : {ui}")


# -------------------------------------------
# Vector Checks
# -------------------------------------------

def check_vectors(storage):

    print_header("VECTOR INDEX")

    dummy = embed("hello world")
    hits = storage.vector.query(dummy, top_k=20)

    print(f"Sample vector hits: {len(hits)}")

    if hits:
        print("\nExample payload:")
        for k, v in hits[0].items():
            print(f"  {k}: {str(v)[:80]}")


# -------------------------------------------
# Chunk Coverage
# -------------------------------------------

def chunk_distribution(storage):

    print_header("CHUNK DISTRIBUTION")

    dummy = embed("test")
    hits = storage.vector.query(dummy, top_k=500)

    per_file = Counter()
    backend = Counter()

    for h in hits:
        f = h.get("file")
        per_file[f] += 1
        if "booklore-backend" in str(f):
            backend[f] += 1

    print(f"Files with chunks: {len(per_file)}")
    print(f"Backend files with chunks: {len(backend)}")

    print("\nTop backend files:")
    for f, c in backend.most_common(10):
        print(f"  {f}: {c}")


# -------------------------------------------
# Retrieval Tests
# -------------------------------------------

def retrieval_test(storage):

    print_header("SEMANTIC RETRIEVAL")

    queries = [
        # Backend-focused
        "spring controller",
        "database repository",
        "hibernate entity",
        "rest api endpoint",
        "authentication service",
        "book repository save method",
        "user login controller",
    ]

    for q in queries:
        print(f"\nQuery: {q}")

        vec = embed(q)
        hits = storage.vector.query(vec, top_k=5)

        if not hits:
            print("  No results")
            continue

        for i, h in enumerate(hits, 1):
            print(f"\n  Result {i}:")
            print(f"    file: {h.get('file')}")
            print(f"    type: {h.get('node_type')}")
            print(f"    sig : {str(h.get('signature'))[:120]}")


# -------------------------------------------
# Main
# -------------------------------------------

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("workspace_id")
    parser.add_argument("--storage", default="~/.sastac")

    args = parser.parse_args()

    base = Path(args.storage).expanduser()
    storage = WorkspaceStorage(args.workspace_id, base)

    check_metadata(storage)
    check_vectors(storage)
    chunk_distribution(storage)
    retrieval_test(storage)


if __name__ == "__main__":
    main()
