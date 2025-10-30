"""Порты (интерфейсы) домена, определяющие границы.

Обязанности:
- Объявление стабильных интерфейсов, от которых зависит приложение.

Ограничения:
- Запрет на импорт из инфраструктуры или фреймворков.
"""

from typing import Any, Dict, List, Mapping, Optional, Protocol

from app.domain.models.track import Track, TrackFormat


class TrackStorage(Protocol):
    def save_raw(self, track: Track, content: bytes) -> str: ...
    def exists(self, track_id: str) -> bool: ...


class TrackIdGenerator(Protocol):
    def new_id(self) -> str: ...


class TrackFormatDetector(Protocol):
    def detect(self, filename: str, first_bytes: bytes) -> Optional[TrackFormat]: ...


class TrackMetadataRepository(Protocol):
    def save(self, meta) -> None: ...


class TrackParser(Protocol):
    def parse(self, format: TrackFormat, blob: bytes) -> dict: ...


class TrackFeatureExtractor(Protocol):
    def extract(self, format: TrackFormat, blob: bytes) -> Mapping[str, Any]: ...


class TrackFeaturesRepository(Protocol):
    def upsert(self, features: Mapping[str, Any]) -> None: ...


class TrackVectorIndex(Protocol):
    def ensure_collection(self, vector_size: int) -> None: ...

    def upsert(self, track_id: str, user_id: int, vector: List[float], payload: Dict[str, Any]) -> None: ...

    def search(
        self, query_vector: List[float], top_k: int = 10, user_id_filter: Optional[int] = None
    ) -> List[Dict[str, Any]]: ...


class TrackVectorizer(Protocol):
    def vector_size(self) -> int: ...
    def vectorize(self, features: Mapping[str, Any]) -> List[float]: ...
