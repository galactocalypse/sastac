import argparse
import random
from pathlib import Path
from collections import Counter, defaultdict

from sentence_transformers import SentenceTransformer
from sastac.storage.scopes.workspace_storage import WorkspaceStorage
from sastac.embedding.embedder import embed

# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def is_vendor(path: str):
    bad = ["vendor", "node_modules", "dist", "build", "assets/foliate"]
    return any(x in path.lower() for x in bad)


def is_backend(path: str):
    p = path.lower()
    return any(x in p for x in [
        "backend", "server", "api", "spring", "repository", "service"
    ])


# -------------------------------------------------------
# Load metadata
# -------------------------------------------------------

def load_files(storage):
    keys = storage.kv.list("file:")
    return {
        storage.kv.get(k)["path"]: storage.kv.get(k)
        for k in keys if storage.kv.get(k)
    }


# -------------------------------------------------------
# Load chunks (random sample)
# -------------------------------------------------------

def load_chunks(storage, sample=2000):
    vec = embed("sample text")
    hits = storage.vector.query(vec, top_k=sample)
    return hits


# -------------------------------------------------------
# Diagnostics
# -------------------------------------------------------

def diagnose_files(files):
    print_section("FILE COVERAGE")

    print(f"Indexed files: {len(files)}")

    langs = Counter(f["language"] for f in files.values())
    for l, c in langs.most_common():
        print(f"  {l}: {c}")

    backend = sum(1 for f in files if is_backend(f))
    print(f"\nBackend files detected: {backend}")

    if backend == 0:
        print("⚠️ Backend not detected → wrong root or language detection.")


def diagnose_chunks(files, chunks):
    print_section("CHUNK COVERAGE")

    per_file = Counter(c.get("file") for c in chunks)
    vendor = sum(1 for c in chunks if is_vendor(c.get("file", "")))
    backend = sum(1 for c in chunks if is_backend(c.get("file", "")))

    print(f"Files with chunks: {len(per_file)}")
    print(f"Backend chunk files: {backend}")
    print(f"Vendor chunks: {vendor}/{len(chunks)}")

    if len(per_file) < len(files) * 0.2:
        print("⚠️ Too few files chunked → parser failing or filters too strict.")

    print("\nTop chunked files:")
    for f, c in per_file.most_common(10):
        print(f"  {c:4}  {f}")


def diagnose_chunk_sizes(chunks):
    print_section("CHUNK SIZE ANALYSIS")

    sizes = [
        c.get("end_line", 0) - c.get("start_line", 0)
        for c in chunks
        if c.get("end_line") is not None
    ]

    if not sizes:
        print("No chunk size data.")
        return

    print(f"Avg lines/chunk: {sum(sizes)/len(sizes):.1f}")
    print(f"Min lines/chunk: {min(sizes)}")
    print(f"Max lines/chunk: {max(sizes)}")

    if min(sizes) > 20:
        print("⚠️ Small functions missing → MIN_CHUNK_SIZE too big.")


def diagnose_embeddings(storage):
    print_section("EMBEDDING DIVERSITY")

    vec1 = embed("database connection")
    vec2 = embed("user authentication")

    diff = sum(abs(a-b) for a, b in zip(vec1, vec2))

    if diff == 0:
        print("❌ Embeddings identical → embedding model broken.")
    else:
        print("Embeddings differ → OK.")


def diagnose_retrieval(storage):
    print_section("SEMANTIC RETRIEVAL")

    queries = [
        "spring controller",
        "database repository",
        "hibernate entity",
        "rest api endpoint",
        "authentication service",
    ]

    for q in queries:
        vec = embed(q)
        hits = storage.vector.query(vec, top_k=5)

        print(f"\nQuery: {q}")
        for h in hits:
            print(" ", h.get("file"))


def diagnose_booklore_specific(files):
    print_section("BOOKLORE CHECKS")

    backend = [
        f for f in files
        if any(x in f.lower() for x in [
            "booklore-api",
            "/src/main/java/",
            "/src/test/java/",
            "/repository/",
            "/service/",
            "/controller/",
            "/model/entity/",
        ])
    ]

    ui = [
        f for f in files
        if any(x in f.lower() for x in [
            "booklore-ui",
            "/src/app/",
            ".tsx",
            ".ts"
        ])
    ]

    print(f"Backend files indexed: {len(backend)}")
    print(f"UI files indexed: {len(ui)}")

    if len(backend) == 0:
        print("⚠️ Backend missing → wrong root path.")


# -------------------------------------------------------
# Main
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
    diagnose_embeddings(storage)
    diagnose_retrieval(storage)
    diagnose_booklore_specific(files)


if __name__ == "__main__":
    main()
