# src/sastac/config/schema.py

from dataclasses import dataclass


@dataclass
class EmbeddingConfig:
    model: str
    vector_size: int


@dataclass
class SastacConfig:
    embeddings: EmbeddingConfig
