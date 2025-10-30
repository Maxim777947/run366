"""Application layer use case: orchestrates steps of business logic.

Responsibilities:
- Coordinate domain and ports to perform a use case.
- No knowledge of technical details of persistence, network, or frameworks.

Constraints:
- Do not import or depend on ORM/SQL/HTTP/Telegram SDKs or any frameworks.
- Depend only on domain entities and ports (protocols) defined in app.domain.
"""

from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from app.domain.models.track import ComputeAndIndexTrackFeaturesCommand, Track
from app.domain.ports.track import (
    TrackFeatureExtractor,
    TrackFeaturesRepository,
    TrackFormatDetector,
    TrackIdGenerator,
    TrackMetadataRepository,
    TrackParser,
    TrackStorage,
    TrackVectorIndex,
    TrackVectorizer,
)


class IngestTrackCommand:
    def __init__(self, user_id: int, filename: str, blob: bytes, source: str = "telegram"):
        self.user_id = user_id
        self.filename = filename
        self.blob = blob
        self.source = source


class IngestTrackUseCase:
    def __init__(
        self,
        storage: TrackStorage,
        id_gen: TrackIdGenerator,
        detector: TrackFormatDetector,
        parser: TrackParser,
        meta_repo: TrackMetadataRepository,
        feature_extractor: TrackFeatureExtractor,
        features_repo: TrackFeaturesRepository,
    ):
        self.storage = storage
        self.id_gen = id_gen
        self.detector = detector
        self.parser = parser
        self.meta_repo = meta_repo
        self.feature_extractor = feature_extractor
        self.features_repo = features_repo

    def execute(self, cmd: IngestTrackCommand) -> Mapping[str, Any]:
        format = self.detector.detect(cmd.filename, cmd.blob[:512])
        if not format:
            raise ValueError("Ожидаю GPX/FIT/TCX")

        track = Track(
            id=self.id_gen.new_id(),
            user_id=cmd.user_id,
            filename=cmd.filename,
            format=format,
            source=cmd.source,
            created_at=datetime.now(timezone.utc),
        )

        self.storage.save_raw(track, cmd.blob)
        meta = self.parser.parse(format, cmd.blob) or {}

        row = {
            "id": track.id,
            "user_id": track.user_id,
            "filename": track.filename,
            "format": track.format.value,
            "source": track.source or "telegram",
            "created_at": track.created_at,
            "distance_km": meta.get("distance_km"),
            "duration_s": meta.get("duration_s"),
            "elevation_gain_m": meta.get("elevation_gain_m"),
        }

        self.meta_repo.save(row)

        feats = dict(self.feature_extractor.extract(format, cmd.blob))
        feats.update({"id": track.id, "user_id": cmd.user_id})
        self.features_repo.upsert(feats)

        return row


class ComputeAndIndexTrackFeaturesUseCase:
    """
    Сценарий application-слоя:
    1) извлечь признаки из бинарного файла;
    2) сохранить признаки в БД (идемпотентно по track_id);
    3) по желанию — построить вектор и проиндексировать в Qdrant.
    """

    def __init__(
        self,
        feature_extractor: TrackFeatureExtractor,
        features_repository: TrackFeaturesRepository,
        vector_index: Optional[TrackVectorIndex] = None,
        track_vectorizer: Optional[TrackVectorizer] = None,
    ) -> None:
        self.feature_extractor = feature_extractor
        self.features_repository = features_repository
        self.vector_index = vector_index
        self.track_vectorizer = track_vectorizer

    def execute(self, command: ComputeAndIndexTrackFeaturesCommand) -> Mapping[str, Any]:
        extracted_track_features: Mapping[str, Any] = self.feature_extractor.extract(
            command.track_format, command.file_bytes
        )
        if not extracted_track_features:
            return {}

        features_to_save = dict(extracted_track_features)
        features_to_save.update({"id": command.track_id})
        self.features_repository.upsert(features_to_save)

        if self.vector_index and self.track_vectorizer:
            features_vector = self.track_vectorizer.vectorize(features_to_save)
            self.vector_index.upsert(
                track_id=command.track_id,
                vector=features_vector,
                payload={
                    "format": command.track_format.value,
                    "start_time": str(features_to_save.get("start_datetime_utc")),
                    "route": features_to_save.get("route_curvature_category"),
                    "terrain": features_to_save.get("terrain_category"),
                    "area": features_to_save.get("start_area_identifier_approx"),
                },
            )

        return features_to_save
