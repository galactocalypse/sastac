# storage/interfaces/vector_store.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class VectorStore(ABC):

    @abstractmethod
    def upsert(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
    ) -> None:
        ...

    @abstractmethod
    def query(
        self,
        vector: List[float],
        top_k: int,
        filters: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        ...
