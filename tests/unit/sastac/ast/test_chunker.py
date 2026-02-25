import pytest

from sastac.ast.chunker import (
    extract_code_chunks,
    CodeChunk,
)


# -----------------------------
# Test: Python recursive extraction
# -----------------------------

PYTHON_SOURCE = """
class A:
    \"\"\"Class docstring\"\"\"

    def foo(self):
        \"\"\"Method docstring\"\"\"
        return 1

def bar():
    return 2
"""


def test_extract_python_chunks_recursive():
    chunks = extract_code_chunks("python", PYTHON_SOURCE)

    # Expect: class A, method foo, function bar
    assert len(chunks) == 3

    names = {c.name for c in chunks}
    assert names == {"A", "foo", "bar"}

    # Validate class chunk
    class_chunk = next(c for c in chunks if c.name == "A")
    assert class_chunk.node_type == "class_definition"
    assert class_chunk.depth == 1
    assert class_chunk.parent_name is None
    assert "class A" in class_chunk.signature
    assert "Class docstring" in (class_chunk.docstring or "")

    # Validate method chunk
    method_chunk = next(c for c in chunks if c.name == "foo")
    assert method_chunk.parent_name == "A"
    assert method_chunk.depth >= 2
    assert "def foo" in method_chunk.signature
    assert "Method docstring" in (method_chunk.docstring or "")

    # Validate standalone function
    bar_chunk = next(c for c in chunks if c.name == "bar")
    assert bar_chunk.parent_name is None
    assert bar_chunk.node_type == "function_definition"


# -----------------------------
# Test: Byte & line offsets
# -----------------------------

def test_chunk_offsets():
    source = "def foo():\n    return 1\n"

    chunks = extract_code_chunks("python", source)
    chunk = chunks[0]

    assert chunk.start_byte == 0
    assert chunk.end_byte <= len(source)

    # Body matches exact byte slice
    assert chunk.body == source[chunk.start_byte:chunk.end_byte]

    # Ensure it captured the function correctly
    assert "def foo()" in chunk.signature


# -----------------------------
# Test: Metadata serialization
# -----------------------------

def test_chunk_metadata_serialization():
    source = "def foo():\n    return 1\n"

    chunk = extract_code_chunks("python", source)[0]
    metadata = chunk.to_metadata()

    assert isinstance(metadata, dict)
    assert metadata["name"] == "foo"
    assert metadata["language"] == "python"


# -----------------------------
# Test: No relevant definitions returns empty
# -----------------------------

def test_no_relevant_nodes():
    source = "x = 1\ny = 2\n"
    chunks = extract_code_chunks("python", source)

    assert chunks == []


# -----------------------------
# Multi-language smoke test
# -----------------------------

@pytest.mark.parametrize(
    "language,source",
    [
        ("javascript", "function foo() { return 1; }"),
        ("typescript", "function foo(): number { return 1; }"),
        ("go", "package main\nfunc main() {}"),
        ("java", "class A { int x; }"),
    ],
)
def test_extract_other_languages(language, source):
    chunks = extract_code_chunks(language, source)

    assert isinstance(chunks, list)
    assert len(chunks) >= 1
    assert isinstance(chunks[0], CodeChunk)
    assert chunks[0].language == language


# -----------------------------
# Test: Nested depth correctness
# -----------------------------

NESTED_SOURCE = """
class Outer:
    class Inner:
        def deep(self):
            return 1
"""


def test_nested_depth_tracking():
    chunks = extract_code_chunks("python", NESTED_SOURCE)

    outer = next(c for c in chunks if c.name == "Outer")
    inner = next(c for c in chunks if c.name == "Inner")
    deep = next(c for c in chunks if c.name == "deep")

    assert outer.depth < inner.depth < deep.depth
    assert inner.parent_name == "Outer"
    assert deep.parent_name == "Inner"
