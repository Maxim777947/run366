from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams


class TrackVectorIndexQdrant:
    """
    Обёртка над Qdrant для индексации и поиска похожих тренировок по вектору признаков.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "track_features_v1",
    ):
        self.collection_name = collection_name
        self.client = QdrantClient(host=host, port=port)

    def ensure_collection(self, vector_size: int) -> None:
        """
        Создаёт коллекцию заново с заданными параметрами (идемпотентно для разработки).
        В проде лучше делать create_collection if not exists.
        """
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    def upsert_track_vector(self, track_id: str, user_id: int, vector: List[float], payload: Dict[str, Any]) -> None:
        """
        Сохраняет (upsert) вектор тренировки c полезной метаинформацией (payload).
        Идентификатор точки — track_id.
        """
        point = PointStruct(id=track_id, vector=vector, payload={"user_id": user_id, **payload})
        self.client.upsert(collection_name=self.collection_name, points=[point])

    def search_similar(
        self,
        query_vector: List[float],
        top_k: int = 10,
        user_id_filter: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Ищет похожие тренировки по косинусному сходству.
        Можно отфильтровать по user_id, чтобы сравнивать только свои тренировки.
        """
        query_filter = None
        if user_id_filter is not None:
            query_filter = Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id_filter))])

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
        )
        # Приводим к удобному формату
        return [{"track_id": r.id, "score": r.score, "payload": r.payload} for r in results]
