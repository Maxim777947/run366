from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

from app.domain.ports.track import TrackVectorIndex


class TrackVectorIndexQdrant(TrackVectorIndex):
    """
    Инфраструктурный репозиторий на базе Qdrant: хранение и поиск векторов признаков треков.
    """

    def __init__(self, host: str = "localhost", port: int = 6333, collection_name: str = "track_features_v1"):
        self.qdrant_client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name

    def ensure_collection(self, vector_size: int) -> None:
        self.qdrant_client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    def upsert(self, track_id: str, vector: List[float], payload: Dict[str, Any]) -> None:
        point = PointStruct(id=track_id, vector=vector, payload={**payload})
        self.qdrant_client.upsert(collection_name=self.collection_name, points=[point])

    def search(
        self, query_vector: List[float], top_k: int = 10, user_id_filter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        query_filter = None
        if user_id_filter is not None:
            query_filter = Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id_filter))])
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
        )
        return [{"track_id": r.id, "score": r.score, "payload": r.payload} for r in results]
