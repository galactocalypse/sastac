# storage/interfaces/kv_store.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class KVStore(ABC):

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        ...

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...

    @abstractmethod
    def list(self, prefix: str = "") -> List[str]:
        ...
