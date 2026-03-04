import argparse
from pathlib import Path
from collections import Counter

from sastac.storage.scopes.workspace_storage import WorkspaceStorage
from sastac.embedding.embedder import embed


# -------------------------------------------
# Helpers
# -------------------------------------------

def print_header(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def extract_payload(hit):
    """
    Handles both flattened and nested payload structures.
    """
    if "payload" in hit:
        return hit["payload"]
    return hit


# -------------------------------------------
# Metadata Checks
# -------------------------------------------

def check_metadata(storage):

    print_header("FILE METADATA")

    keys = storage.kv.list("file:")
    print(f"Indexed files: {len(keys)}")

    langs = Counter()

    for k in keys:
        meta = storage.kv.get(k)
        if not meta:
            continue
        langs[meta.get("language")] += 1

    print("\nLanguages:")
    for lang, count in langs.most_common():
        print(f"  {lang}: {count}")


# -------------------------------------------
# Vector Checks
# -------------------------------------------

def check_vectors(storage):

    print_header("VECTOR INDEX")

    dummy = embed("hello world")
    hits = storage.vector.query(dummy, top_k=10)

    print(f"Sample vector hits: {len(hits)}")

    if hits:
        payload = extract_payload(hits[0])

        print("\nExample payload:")
        for k, v in payload.items():
            print(f"  {k}: {str(v)[:100]}")


# -------------------------------------------
# Chunk Coverage
# -------------------------------------------

def chunk_distribution(storage):

    print_header("CHUNK DISTRIBUTION")

    # Instead of semantic query, fetch many random-ish hits
    dummy = embed("code")
    hits = storage.vector.query(dummy, top_k=1000)

    per_file = Counter()
    node_types = Counter()

    for h in hits:
        payload = extract_payload(h)

        f = payload.get("file")
        per_file[f] += 1
        node_types[payload.get("node_type")] += 1

    print(f"Files with chunks (sampled): {len(per_file)}")

    print("\nTop files (sampled):")
    for f, c in per_file.most_common(10):
        print(f"  {f}: {c}")

    print("\nNode type distribution (sampled):")
    for t, c in node_types.most_common():
        print(f"  {t}: {c}")


# -------------------------------------------
# Retrieval Tests
# -------------------------------------------

def retrieval_test(storage):

    print_header("SEMANTIC RETRIEVAL")

    queries = [
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
            payload = extract_payload(h)

            print(f"\n  Result {i}:")
            print(f"    file: {payload.get('file')}")
            print(f"    type: {payload.get('node_type')}")
            print(f"    tags: {payload.get('tags')}")
            print(f"    signature: {str(payload.get('signature'))[:120]}")


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
