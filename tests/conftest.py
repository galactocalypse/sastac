# tests/conftest.py

import pytest
from pathlib import Path
from typing import Generator

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
    """
    Override environment variables for test isolation.
    """
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("EMBEDDING_MODEL", "test-embed-model")
    monkeypatch.setenv("MAX_CONTEXT_TOKENS", "2048")


# ---- Mock LLM Client ----

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


# ---- In-Memory Vector Store ----

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


# ---- Sample Repository Fixture ----

@pytest.fixture
def sample_repo(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_repo"


# ---- Temporary Working Directory ----

@pytest.fixture
def temp_workdir(tmp_path: Path) -> Generator[Path, None, None]:
    yield tmp_path
