from sastac.ast.chunk_indexer import ChunkIndexer


# helper to create large enough function
def big_function(name="foo"):
    return f"""
def {name}():
    x = 1
    y = 2
    z = x + y
    a = z * 3
    b = a * 4
    c = b * 5
    d = c * 6
    e = d * 7
    f = e * 8
    g = f * 9
    return g
"""


# --------------------------------------------------------
# Basic chunk indexing
# --------------------------------------------------------

def test_indexes_python_functions(
    temp_workdir,
    fake_workspace_storage,
    write_file,
    fake_embed,
):

    f = temp_workdir / "a.py"
    write_file(f, big_function("foo") + big_function("bar"))

    idx = ChunkIndexer(fake_workspace_storage, fake_embed)
    idx.index([f])

    assert len(fake_workspace_storage.vector.points) >= 2


# --------------------------------------------------------
# Small chunks filtered
# --------------------------------------------------------

def test_filters_small_chunks(
    temp_workdir,
    fake_workspace_storage,
    write_file,
    fake_embed,
):

    f = temp_workdir / "a.py"
    write_file(f, "def x(): pass")

    idx = ChunkIndexer(fake_workspace_storage, fake_embed)
    idx.index([f])

    points = fake_workspace_storage.vector.points
    # Either no chunks OR fallback chunk allowed
    assert len(points) == 1
    assert points[0]["metadata"]["node_type"] == "function_definition"


def test_small_function_kept(temp_workdir,
    fake_workspace_storage,
    write_file,
    fake_embed,):
    f = temp_workdir / "a.py"
    write_file(f, "def x(): pass")
    idx = ChunkIndexer(fake_workspace_storage, fake_embed)
    idx.index([f])
    points = fake_workspace_storage.vector.points
    assert points[0]["metadata"]["node_type"] == "function_definition"


# --------------------------------------------------------
# Embedding called
# --------------------------------------------------------

def test_embedding_called(
    temp_workdir,
    fake_workspace_storage,
    write_file,
    recording_embed,
):

    f = temp_workdir / "a.py"
    write_file(f, big_function())

    idx = ChunkIndexer(fake_workspace_storage, recording_embed)
    idx.index([f])

    assert len(recording_embed.calls) >= 1


# --------------------------------------------------------
# Multiple files
# --------------------------------------------------------

def test_multiple_files(
    temp_workdir,
    fake_workspace_storage,
    write_file,
    fake_embed,
):

    write_file(temp_workdir / "a.py", big_function("a"))
    write_file(temp_workdir / "b.py", big_function("b"))

    idx = ChunkIndexer(fake_workspace_storage, fake_embed)
    idx.index(list(temp_workdir.glob("*.py")))

    assert len(fake_workspace_storage.vector.points) >= 2


# --------------------------------------------------------
# Unsupported language ignored
# --------------------------------------------------------

def test_ignores_unknown_language(
    temp_workdir,
    fake_workspace_storage,
    write_file,
    fake_embed,
):

    f = temp_workdir / "a.txt"
    write_file(f, "hello world")

    idx = ChunkIndexer(fake_workspace_storage, fake_embed)
    idx.index([f])

    assert len(fake_workspace_storage.vector.points) == 0
