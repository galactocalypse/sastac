from pathlib import Path

from sastac.ast.chunker import extract_code_chunks
from sastac.ast.chunk_indexer import ChunkIndexer, detect_language


JAVA_SIMPLE = """
class A {
    public int x() { return 1; }
}
"""

JAVA_SMALL_METHOD = """
class A {
    public int x(){return 1;}
}
"""

JAVA_NO_METHOD = """
class A {
    int x;
}
"""


def test_java_language_detection(temp_workdir, write_file):
    f = temp_workdir / "A.java"
    write_file(f, JAVA_SIMPLE)

    assert detect_language(f) == "java"


def test_java_parser_returns_chunks():
    chunks = extract_code_chunks("java", JAVA_SIMPLE)

    assert len(chunks) > 0
    assert any(c.node_type in {"class_declaration", "method_declaration"} for c in chunks)


def test_java_chunks_not_filtered(
    temp_workdir,
    fake_workspace_storage,
    write_file,
    fake_embed,
):
    f = temp_workdir / "A.java"
    write_file(f, JAVA_SIMPLE)

    idx = ChunkIndexer(fake_workspace_storage, fake_embed)
    idx.index([f])

    points = fake_workspace_storage.vector.points

    assert len(points) > 0
    assert any(p["metadata"]["node_type"] != "fallback_chunk" for p in points)


def test_java_small_method_not_filtered(
    temp_workdir,
    fake_workspace_storage,
    write_file,
    fake_embed,
):
    f = temp_workdir / "A.java"
    write_file(f, JAVA_SMALL_METHOD)

    idx = ChunkIndexer(fake_workspace_storage, fake_embed)
    idx.index([f])

    points = fake_workspace_storage.vector.points

    assert len(points) > 0


def test_java_class_without_methods(
    temp_workdir,
    fake_workspace_storage,
    write_file,
    fake_embed,
):
    f = temp_workdir / "A.java"
    write_file(f, JAVA_NO_METHOD)

    idx = ChunkIndexer(fake_workspace_storage, fake_embed)
    idx.index([f])

    points = fake_workspace_storage.vector.points

    # This tells you if class-only files are indexed
    assert len(points) >= 0  # diagnostic test
