# storage/backends/qdrant_vector.py

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sastac.storage.interfaces.vector_store import VectorStore
from typing import Dict, Any, List
from typing import Dict, Any, List
from qdrant_client.models import Filter, FieldCondition, MatchValue
from typing import Iterable
import uuid
from qdrant_client.models import PointIdsList
from typing import List, cast
from qdrant_client.models import PointIdsList, ExtendedPointId


class QdrantVectorStore(VectorStore):

    def __init__(self, collection: str, path: str, vector_size: int):
        self.client = QdrantClient(path=path)
        self.collection = collection
        self.vector_size = vector_size
        self._ensure_collection()

    def upsert(self, ids, vectors, metadata):
        points = [
            PointStruct(id=i, vector=v, payload=m)
            for i, v, m in zip(ids, vectors, metadata)
        ]
        self.client.upsert(collection_name=self.collection, points=points)


    def query(self, vector, top_k, filters=None) -> List[Dict[str, Any]]:
        filter_obj = _build_filter(filters)

        hits = self.client.query_points(
            collection_name=self.collection,
            query=vector,
            limit=top_k,
            query_filter=filter_obj,
        ).points

        results: List[Dict[str, Any]] = []
        for h in hits:
            results.append(dict(h.payload or {}))

        return results

    def delete(self, ids: Iterable):
        normalized: List[ExtendedPointId] = cast(
            List[ExtendedPointId],
            [_normalize_id(i) for i in ids],
        )

        self.client.delete(
            collection_name=self.collection,
            points_selector=PointIdsList(points=normalized),
        )

    def _ensure_collection(self):
        if self.collection not in [
            c.name for c in self.client.get_collections().collections
        ]:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )
    
def _build_filter(filters: Dict[str, Any] | None) -> Filter | None:
    if not filters:
        return None

    return Filter(
        must=[
            FieldCondition(
                key=k,
                match=MatchValue(value=v),
            )
            for k, v in filters.items()
        ]
    )


def _normalize_id(i):
    if isinstance(i, uuid.UUID):
        return i
    try:
        return uuid.UUID(str(i))
    except Exception:
        return uuid.uuid4()
