# test_embed_integration.py
"""
Integration Tests for the Ollama bge-m3 embed() function.

These tests make **real** calls to your local Ollama server.
No mocks — they validate actual embedding quality.

Prerequisites (run once):
1. Ollama server running: `ollama serve` (in a separate terminal)
2. Model pulled: `ollama pull bge-m3`

Run with:
    pip install pytest          # (if not already installed)
    pytest test_embed_integration.py -m integration -v
"""

import pytest
import ollama
from sastac.embedding.embedder import embed


def is_ollama_and_model_ready() -> bool:
    """Check Ollama server + bge-m3 model availability."""
    try:
        client = ollama.Client()
        # Quick health check
        models = [m.model for m in client.list()["models"]]
        return any(name.startswith("bge-m3") for name in models)
    except Exception:
        return False


# ====================== Integration Tests ======================

@pytest.mark.integration
@pytest.mark.skipif(
    not is_ollama_and_model_ready(),
    reason="Ollama server not running or bge-m3 not pulled. "
           "Run: ollama serve && ollama pull bge-m3"
)
def test_embed_single_string():
    """Single string → 1024-dim vector (bge-m3)."""
    result = embed("This is a test sentence for Ollama integration.")

    assert isinstance(result, list)
    assert len(result) == 1024, f"Expected 1024 dimensions, got {len(result)}"
    assert all(isinstance(x, float) for x in result)
    assert any(abs(x) > 1e-5 for x in result), "Embedding vector should not be all zeros"


@pytest.mark.integration
@pytest.mark.skipif(not is_ollama_and_model_ready(), reason="Ollama / bge-m3 not ready")
def test_embed_batch():
    """List of strings → list of embeddings."""
    texts = [
        "Hello, how are you?",
        "The weather is nice today.",
        "Machine learning embeddings are powerful."
    ]
    result = embed(texts)

    assert isinstance(result, list)
    assert len(result) == 3
    assert all(len(vec) == 1024 for vec in result)


@pytest.mark.integration
@pytest.mark.skipif(not is_ollama_and_model_ready(), reason="Ollama / bge-m3 not ready")
def test_deterministic_embedding():
    """Same text must always produce identical embedding."""
    text = "Deterministic test for bge-m3 via Ollama."
    emb1 = embed(text)
    emb2 = embed(text)
    assert emb1 == emb2


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Pure Python cosine similarity (no extra dependencies)."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    return dot / (norm_a * norm_b + 1e-8)


@pytest.mark.integration
@pytest.mark.skipif(not is_ollama_and_model_ready(), reason="Ollama / bge-m3 not ready")
def test_semantic_similarity():
    """Similar sentences → high cosine similarity, dissimilar → low."""
    vec1 = embed("The cat is sleeping on the couch.")
    vec2 = embed("A kitten is resting on the sofa.")
    vec3 = embed("The stock market rose sharply yesterday.")

    sim_similar = cosine_similarity(vec1, vec2)
    sim_different = cosine_similarity(vec1, vec3)

    assert sim_similar > 0.65, f"Similar sentences similarity too low: {sim_similar:.3f}"
    assert sim_different < 0.45, f"Dissimilar sentences similarity too high: {sim_different:.3f}"


@pytest.mark.integration
@pytest.mark.skipif(not is_ollama_and_model_ready(), reason="Ollama / bge-m3 not ready")
def test_empty_list():
    """Empty list input returns empty list."""
    result = embed([])
    assert result == []
