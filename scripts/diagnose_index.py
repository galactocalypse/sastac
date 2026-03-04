import argparse
from pathlib import Path
from collections import Counter

from sastac.storage.scopes.workspace_storage import WorkspaceStorage
from sastac.embedding.embedder import embed


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def extract_payload(hit):
    """
    Supports both flattened and nested vector store payloads.
    """
    if "payload" in hit:
        return hit["payload"]
    return hit


# -------------------------------------------------------
# Load metadata
# -------------------------------------------------------

def load_files(storage):
    keys = storage.kv.list("file:")
    files = {}

    for k in keys:
        meta = storage.kv.get(k)
        if meta and meta.get("path"):
            files[meta["path"]] = meta

    return files


# -------------------------------------------------------
# Load chunks (sampled)
# -------------------------------------------------------

def load_chunks(storage, sample=2000):
    vec = embed("diagnostic probe")
    hits = storage.vector.query(vec, top_k=sample)
    return [extract_payload(h) for h in hits]


# -------------------------------------------------------
# FILE COVERAGE
# -------------------------------------------------------

def diagnose_files(files):

    print_section("FILE COVERAGE")

    print(f"Indexed files: {len(files)}")

    langs = Counter(f.get("language") for f in files.values())
    print("\nLanguage distribution:")
    for l, c in langs.most_common():
        print(f"  {l}: {c}")

    if not langs:
        print("❌ No languages detected → indexing failed.")


# -------------------------------------------------------
# CHUNK COVERAGE
# -------------------------------------------------------

def diagnose_chunks(files, chunks):

    print_section("CHUNK COVERAGE")

    per_file = Counter(c.get("file") for c in chunks if c.get("file"))
    node_types = Counter(c.get("node_type") for c in chunks if c.get("node_type"))
    tags = Counter(
        tag
        for c in chunks
        for tag in (c.get("tags") or [])
    )

    print(f"Files with chunks (sampled): {len(per_file)}")
    print(f"Total sampled chunks: {len(chunks)}")

    coverage_ratio = len(per_file) / max(len(files), 1)
    print(f"File-to-chunk coverage ratio: {coverage_ratio:.2f}")

    if coverage_ratio < 0.2:
        print("⚠️ Low coverage → parser failing or filters too strict.")

    print("\nTop chunked files (sampled):")
    for f, c in per_file.most_common(10):
        print(f"  {c:4}  {f}")

    print("\nNode type distribution:")
    for t, c in node_types.most_common():
        print(f"  {t}: {c}")

    if tags:
        print("\nTag distribution:")
        for t, c in tags.most_common():
            print(f"  {t}: {c}")


# -------------------------------------------------------
# CHUNK SIZE ANALYSIS
# -------------------------------------------------------

def diagnose_chunk_sizes(chunks):

    print_section("CHUNK SIZE ANALYSIS")

    sizes = [
        (c.get("end_line", 0) - c.get("start_line", 0))
        for c in chunks
        if c.get("start_line") is not None and c.get("end_line") is not None
    ]

    if not sizes:
        print("No chunk size data available.")
        return

    avg = sum(sizes) / len(sizes)
    print(f"Avg lines/chunk: {avg:.1f}")
    print(f"Min lines/chunk: {min(sizes)}")
    print(f"Max lines/chunk: {max(sizes)}")

    if max(sizes) > 500:
        print("⚠️ Large chunks detected → splitting may be insufficient.")

    if min(sizes) == 0:
        print("⚠️ Zero-length chunks present.")


# -------------------------------------------------------
# ANNOTATION PRESENCE
# -------------------------------------------------------

def diagnose_annotations(chunks):

    print_section("ANNOTATION / METADATA PRESENCE")

    class_ann = sum(1 for c in chunks if c.get("class_annotations"))
    method_ann = sum(1 for c in chunks if c.get("method_annotations"))

    print(f"Chunks with class annotations: {class_ann}")
    print(f"Chunks with method annotations: {method_ann}")

    if class_ann == 0:
        print("⚠️ No class annotations detected → annotation extraction may be broken.")


# -------------------------------------------------------
# EMBEDDING DIVERSITY
# -------------------------------------------------------

def diagnose_embeddings():

    print_section("EMBEDDING DIVERSITY")

    vec1 = embed("database connection")
    vec2 = embed("user authentication")

    diff = sum(abs(a - b) for a, b in zip(vec1, vec2))

    if diff == 0:
        print("❌ Embeddings identical → embedding model broken.")
    else:
        print("Embeddings differ → OK.")


# -------------------------------------------------------
# SEMANTIC RETRIEVAL
# -------------------------------------------------------

def diagnose_retrieval(storage):

    print_section("SEMANTIC RETRIEVAL")

    queries = [
        "controller class",
        "repository interface",
        "entity model",
        "authentication logic",
        "api endpoint",
    ]

    for q in queries:
        vec = embed(q)
        hits = storage.vector.query(vec, top_k=5)

        print(f"\nQuery: {q}")

        if not hits:
            print("  No results")
            continue

        for h in hits:
            p = extract_payload(h)
            print(" ", p.get("file"), "|", p.get("node_type"))


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("workspace_id")
    parser.add_argument("--storage", default="~/.sastac")
    args = parser.parse_args()

    storage = WorkspaceStorage(
        args.workspace_id,
        Path(args.storage).expanduser()
    )

    files = load_files(storage)
    chunks = load_chunks(storage)

    diagnose_files(files)
    diagnose_chunks(files, chunks)
    diagnose_chunk_sizes(chunks)
    diagnose_annotations(chunks)
    diagnose_embeddings()
    diagnose_retrieval(storage)


if __name__ == "__main__":
    main()
