from pathlib import Path

from sastac.ast.chunker import extract_code_chunks
from sastac.ast.chunk_indexer import MIN_CHUNK_SIZE, MAX_CHUNK_SIZE


# ------------------------------------------------------------
# ⚠️ Change this to a real Booklore backend file
# ------------------------------------------------------------
JAVA_FILE = Path(
    "/home/adarsh/code/booklore/booklore-api/src/main/java/org/booklore/service/reader/CbxReaderService.java"
)


def test_dump_java_chunks():

    assert JAVA_FILE.exists(), f"File not found: {JAVA_FILE}"

    source = JAVA_FILE.read_text()

    chunks = extract_code_chunks("java", source)

    print("\n==============================")
    print("JAVA FILE:", JAVA_FILE)
    print("TOTAL CHUNKS FOUND:", len(chunks))
    print("==============================\n")

    if not chunks:
        print("❌ No AST chunks extracted → parser issue")
        assert False

    kept = 0
    skipped_small = 0
    skipped_large = 0

    for i, c in enumerate(chunks, 1):

        size = len(c.body)

        status = "KEPT"

        if size < MIN_CHUNK_SIZE:
            status = "SKIPPED_SMALL"
            skipped_small += 1

        elif size > MAX_CHUNK_SIZE:
            status = "SKIPPED_LARGE"
            skipped_large += 1

        else:
            kept += 1

        print(f"\n--- Chunk {i}")
        print("node_type:", c.node_type)
        print("name     :", c.name)
        print("lines    :", c.start_line, "-", c.end_line)
        print("size     :", size)
        print("status   :", status)
        print("signature:", c.signature[:120])

    print("\n==============================")
    print("SUMMARY")
    print("==============================")
    print("Total chunks :", len(chunks))
    print("Kept         :", kept)
    print("Skipped small:", skipped_small)
    print("Skipped large:", skipped_large)

    # This test never fails automatically — it's diagnostic
    assert True
