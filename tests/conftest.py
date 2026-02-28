# tests/conftest.py

import pytest
from pathlib import Path
from typing import Generator, List, Any
import uuid


# ---- Paths ----

@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def fixtures_dir(project_root: Path) -> Path:
    return project_root / "tests" / "fixtures"


# ---- Test Settings Override ----

@pytest.fixture(autouse=True)
def test_env(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("EMBEDDING_MODEL", "test-embed-model")
    monkeypatch.setenv("MAX_CONTEXT_TOKENS", "2048")


# ============================================================
# Fake Workspace Storage
# ============================================================

class FakeKVStore:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value

    def delete(self, key):
        self.data.pop(key, None)

    def list(self, prefix=""):
        return [k for k in self.data if k.startswith(prefix)]


class FakeVectorStore:
    def __init__(self):
        self.points = []
        self.vector_size = 3

    def upsert(self, ids: List[Any], vectors: List[Any], metadata: List[Any]):
        for i, v, m in zip(ids, vectors, metadata):
            self.points.append({
                "id": i,
                "vector": v,
                "metadata": m,
            })

    def query(self, *args, **kwargs):
        return self.points

    def delete(self, ids):
        ids = set(ids)
        self.points = [p for p in self.points if p["id"] not in ids]


class FakeWorkspaceStorage:
    def __init__(self):
        self.kv = FakeKVStore()
        self.vector = FakeVectorStore()


@pytest.fixture
def fake_workspace_storage():
    return FakeWorkspaceStorage()


# ============================================================
# Fake Embeddings
# ============================================================

@pytest.fixture
def fake_embed():
    def embed(text: str):
        return [1.0, 2.0, 3.0]
    return embed


@pytest.fixture
def recording_embed():
    calls = []

    def embed(text: str):
        calls.append(text)
        return [0.1, 0.2, 0.3]

    embed.calls = calls
    return embed


# ============================================================
# Fake LLM Client
# ============================================================

class FakeLLM:
    def __init__(self):
        self.calls = []

    async def generate(self, prompt: str) -> str:
        self.calls.append(prompt)
        return "MOCK_RESPONSE"

    def generate_sync(self, prompt: str) -> str:
        self.calls.append(prompt)
        return "MOCK_RESPONSE"


@pytest.fixture
def fake_llm():
    return FakeLLM()


# ============================================================
# In-Memory Vector Store (legacy compatibility)
# ============================================================

class InMemoryVectorStore:
    def __init__(self):
        self.store = []

    def add(self, item):
        self.store.append(item)

    def search(self, query, k=5):
        return self.store[:k]


@pytest.fixture
def in_memory_vector_store():
    return InMemoryVectorStore()


# ============================================================
# Sample Repository Fixture
# ============================================================

@pytest.fixture
def sample_repo(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_repo"


# ============================================================
# Temporary Working Directory
# ============================================================

@pytest.fixture
def temp_workdir(tmp_path: Path) -> Generator[Path, None, None]:
    yield tmp_path


# ============================================================
# Helper: Create Sample Files
# ============================================================

@pytest.fixture
def write_file():
    def _write(path: Path, text: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return _write
