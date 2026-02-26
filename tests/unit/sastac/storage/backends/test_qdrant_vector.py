import uuid
import pytest

from sastac.storage.backends.qdrant_vector import QdrantVectorStore


VECTOR_DIM = 8


def v(i):
    """Deterministic orthogonal vector"""
    vec = [0.0] * VECTOR_DIM
    vec[i] = 1.0
    return vec


@pytest.fixture
def collection_name():
    return f"test_collection_{uuid.uuid4().hex}"


@pytest.fixture
def vector_store(collection_name, tmp_path):
    store = QdrantVectorStore(
        collection=collection_name,
        path=str(tmp_path / "qdrant"),
        vector_size=VECTOR_DIM,
    )
    yield store
    store.client.close()   # avoid shutdown warning


def test_upsert_and_query(vector_store):
    ids = [uuid.uuid4(), uuid.uuid4()]

    vectors = [
        v(0),   # a.py
        v(1),   # b.py
    ]

    metadata = [
        {"file": "a.py", "symbol": "foo"},
        {"file": "b.py", "symbol": "bar"},
    ]

    vector_store.upsert(ids, vectors, metadata)

    result = vector_store.query(v(0), top_k=1)

    assert len(result) == 1
    assert result[0]["file"] == "a.py"


def test_delete(vector_store):
    ids = [uuid.uuid4()]
    vectors = [v(2)]
    metadata = [{"file": "c.py"}]

    vector_store.upsert(ids, vectors, metadata)
    vector_store.delete(ids)

    result = vector_store.query(v(2), top_k=5)
    assert all(r.get("file") != "c.py" for r in result)


def test_multiple_upserts(vector_store):
    id1 = uuid.uuid4()

    vector_store.upsert(
        [id1],
        [v(3)],
        [{"file": "x.py"}],
    )

    vector_store.upsert(
        [id1],
        [v(4)],
        [{"file": "x2.py"}],
    )

    result = vector_store.query(v(4), top_k=1)
    assert result[0]["file"] == "x2.py"


def test_filter_query(vector_store):
    ids = [uuid.uuid4(), uuid.uuid4()]

    vectors = [
        v(5),
        v(6),
    ]

    metadata = [
        {"file": "a.py", "lang": "python"},
        {"file": "b.ts", "lang": "typescript"},
    ]

    vector_store.upsert(ids, vectors, metadata)

    result = vector_store.query(
        v(6),
        top_k=5,
        filters={"lang": "typescript"},
    )

    assert len(result) == 1
    assert result[0]["file"] == "b.ts"
