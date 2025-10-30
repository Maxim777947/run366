from qdrant_client import QdrantClient, models

from app.config import settings

client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)


def init_qdrant():
    try:
        client.get_collection(settings.QDRANT_COLLECTION)
    except Exception:
        client.recreate_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=models.VectorParams(
                size=settings.EMBEDDING_DIM,
                distance=models.Distance.COSINE,
                hnsw_config=models.HnswConfigDiff(
                    m=16,
                    ef_construct=100,
                    full_scan_threshold=10_000,
                ),
            ),
            optimizers_config=models.OptimizersConfigDiff(default_segment_number=2),
        )
