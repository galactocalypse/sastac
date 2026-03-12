# src/sastac/config/schema.py

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EmbeddingConfig:
    model: str
    vector_size: int

@dataclass
class LLMConfig:
    model: str
    temperature: float

@dataclass
class SastacConfig:
    embeddings: EmbeddingConfig
    task_refiner: Optional[LLMConfig] = None
    task_planner: Optional[LLMConfig] = None
