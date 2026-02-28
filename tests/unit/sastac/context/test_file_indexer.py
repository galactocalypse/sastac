import time
from pathlib import Path

from sastac.context.file_indexer import FileIndexer


# --------------------------------------------------------
# Basic indexing
# --------------------------------------------------------

def test_indexes_allowed_files(temp_workdir, fake_workspace_storage, write_file):

    write_file(temp_workdir / "a.py", "print(1)")
    write_file(temp_workdir / "b.js", "function x(){}")
    write_file(temp_workdir / "c.txt", "ignore")

    idx = FileIndexer(fake_workspace_storage)
    files = idx.index(temp_workdir)

    assert len(files) == 2
    assert len(fake_workspace_storage.kv.data) == 2


# --------------------------------------------------------
# Skip directories
# --------------------------------------------------------

def test_skips_node_modules_and_git(temp_workdir, fake_workspace_storage, write_file):

    write_file(temp_workdir / "node_modules/a.py", "print(1)")
    write_file(temp_workdir / ".git/b.py", "print(1)")
    write_file(temp_workdir / "src/c.py", "print(1)")

    idx = FileIndexer(fake_workspace_storage)
    files = idx.index(temp_workdir)

    assert len(files) == 1
    assert "src/c.py" in str(files[0])


# --------------------------------------------------------
# Skip large files
# --------------------------------------------------------

def test_skips_large_files(temp_workdir, fake_workspace_storage, write_file):

    big = temp_workdir / "big.py"
    write_file(big, "x" * 300_000)

    idx = FileIndexer(fake_workspace_storage)
    files = idx.index(temp_workdir)

    assert files == []
    assert fake_workspace_storage.kv.data == {}


# --------------------------------------------------------
# Metadata correctness
# --------------------------------------------------------

def test_metadata_written(temp_workdir, fake_workspace_storage, write_file):

    f = temp_workdir / "a.py"
    write_file(f, "print(1)")

    idx = FileIndexer(fake_workspace_storage)
    idx.index(temp_workdir)

    stored = list(fake_workspace_storage.kv.data.values())[0]

    assert stored["path"].endswith("a.py")
    assert stored["language"] == "python"
    assert stored["size"] > 0
    assert "hash" in stored
    assert "indexed_at" in stored


# --------------------------------------------------------
# Hash change detection
# --------------------------------------------------------

def test_reindexes_when_file_changes(temp_workdir, fake_workspace_storage, write_file):

    f = temp_workdir / "a.py"
    write_file(f, "print(1)")

    idx = FileIndexer(fake_workspace_storage)
    idx.index(temp_workdir)

    first_hash = list(fake_workspace_storage.kv.data.values())[0]["hash"]

    time.sleep(0.01)
    write_file(f, "print(2)")
    idx.index(temp_workdir)

    second_hash = list(fake_workspace_storage.kv.data.values())[0]["hash"]

    assert first_hash != second_hash


# --------------------------------------------------------
# Incremental indexing (no change)
# --------------------------------------------------------

def test_skips_when_hash_same(temp_workdir, fake_workspace_storage, write_file):

    f = temp_workdir / "a.py"
    write_file(f, "print(1)")

    idx = FileIndexer(fake_workspace_storage)
    idx.index(temp_workdir)

    first_store = fake_workspace_storage.kv.data.copy()
    idx.index(temp_workdir)

    assert fake_workspace_storage.kv.data == first_store


# --------------------------------------------------------
# Max files limit
# --------------------------------------------------------

def test_respects_max_files_limit(monkeypatch, temp_workdir, fake_workspace_storage, write_file):

    from sastac.context import file_indexer as fi

    monkeypatch.setattr(fi, "MAX_FILES", 3)

    for i in range(10):
        write_file(temp_workdir / f"{i}.py", "print(1)")

    idx = FileIndexer(fake_workspace_storage)
    files = idx.index(temp_workdir)

    assert len(files) == 3
