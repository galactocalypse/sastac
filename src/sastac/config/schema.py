# src/sastac/config/schema.py

from dataclasses import dataclass


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
    task_refiner: LLMConfig
    task_planner: LLMConfig
