import time
from pathlib import Path

from sastac.context.workspace_indexer import WorkspaceIndexer
from sastac.ast.chunk_indexer import ChunkIndexer


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Test Class
# ------------------------------------------------------------

class TestWorkspaceIndexer:

    # ------------------------------------------
    # File indexing
    # ------------------------------------------

    def test_indexes_files(
        self,
        temp_workdir,
        fake_workspace_storage,
        write_file,
    ):
        write_file(temp_workdir / "a.py", "print(1)")
        write_file(temp_workdir / "b.txt", "ignore")

        idx = WorkspaceIndexer.__new__(WorkspaceIndexer)
        idx.storage = fake_workspace_storage

        files = idx.index_files(temp_workdir)

        assert len(files) == 1
        assert len(fake_workspace_storage.kv.data) == 1


    # ------------------------------------------
    # Chunk indexing
    # ------------------------------------------

    def test_indexes_chunks(
        self,
        temp_workdir,
        fake_workspace_storage,
        write_file,
        fake_embed,
    ):
        f = temp_workdir / "a.py"
        write_file(f, big_function())

        idx = WorkspaceIndexer.__new__(WorkspaceIndexer)
        idx.storage = fake_workspace_storage
        idx.chunk_indexer = ChunkIndexer(fake_workspace_storage, fake_embed)

        idx.index_chunks([f])

        assert len(fake_workspace_storage.vector.points) >= 1


    # ------------------------------------------
    # Full pipeline
    # ------------------------------------------

    def test_build_pipeline(
        self,
        temp_workdir,
        fake_workspace_storage,
        write_file,
        fake_embed
    ):
        f = temp_workdir / "a.py"
        write_file(f, big_function())

        idx = WorkspaceIndexer.__new__(WorkspaceIndexer)
        idx.storage = fake_workspace_storage
        idx.chunk_indexer = ChunkIndexer(fake_workspace_storage, fake_embed)

        idx.build(temp_workdir)

        assert len(fake_workspace_storage.kv.data) == 1
        assert len(fake_workspace_storage.vector.points) >= 1


    # ------------------------------------------
    # Skip large file
    # ------------------------------------------

    def test_skip_large_file(
        self,
        monkeypatch,
        temp_workdir,
        fake_workspace_storage,
        write_file,
    ):
        from sastac.context import workspace_indexer as wi
        monkeypatch.setattr(wi, "MAX_FILE_SIZE", 100)

        write_file(temp_workdir / "big.py", "x" * 500)

        idx = WorkspaceIndexer.__new__(WorkspaceIndexer)
        idx.storage = fake_workspace_storage

        files = idx.index_files(temp_workdir)

        assert files == []
        assert fake_workspace_storage.kv.data == {}


    # ------------------------------------------
    # Skip dirs
    # ------------------------------------------

    def test_skip_node_modules(
        self,
        temp_workdir,
        fake_workspace_storage,
        write_file,
    ):
        write_file(temp_workdir / "node_modules/a.py", "print(1)")
        write_file(temp_workdir / "src/b.py", "print(1)")

        idx = WorkspaceIndexer.__new__(WorkspaceIndexer)
        idx.storage = fake_workspace_storage

        files = idx.index_files(temp_workdir)

        assert len(files) == 1


    # ------------------------------------------
    # Incremental indexing
    # ------------------------------------------

    def test_reindex_on_change(
        self,
        temp_workdir,
        fake_workspace_storage,
        write_file,
    ):
        f = temp_workdir / "a.py"
        write_file(f, "print(1)")

        idx = WorkspaceIndexer.__new__(WorkspaceIndexer)
        idx.storage = fake_workspace_storage

        idx.index_files(temp_workdir)
        first_hash = list(fake_workspace_storage.kv.data.values())[0]["hash"]

        time.sleep(0.01)
        write_file(f, "print(2)")
        idx.index_files(temp_workdir)

        second_hash = list(fake_workspace_storage.kv.data.values())[0]["hash"]
        assert first_hash != second_hash


    # ------------------------------------------
    # Limit files
    # ------------------------------------------

    def test_max_files_limit(
        self,
        monkeypatch,
        temp_workdir,
        fake_workspace_storage,
        write_file,
    ):
        from sastac.context import workspace_indexer as wi
        monkeypatch.setattr(wi, "MAX_FILES", 2)

        for i in range(5):
            write_file(temp_workdir / f"{i}.py", "print(1)")

        idx = WorkspaceIndexer.__new__(WorkspaceIndexer)
        idx.storage = fake_workspace_storage

        files = idx.index_files(temp_workdir)
        assert len(files) == 2
