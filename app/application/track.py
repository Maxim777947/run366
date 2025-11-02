"""
Слой аппликации, реализация сценариев
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional

from app.domain.models.track import ComputeAndIndexTrackFeaturesCommand, RecommendRoutesCommand, Track
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
from app.domain.ports.user import UserRepository


class IngestTrackCommand:
    def __init__(self, user_id: int, filename: str, blob: bytes, source: str = "telegram"):
        self.user_id = user_id
        self.filename = filename
        self.blob = blob
        self.source = source


class IngestTrackUseCase:
    """Загрузка файлов GPX и подсчёт основных метрик"""

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
                    "distance": features_to_save.get("total_distance_kilometers"),
                    "hour": features_to_save.get("start_hour_of_day_utc"),
                },
            )

        return features_to_save


class RecommendRoutesUseCase:
    """
    Сценарий: рекомендация маршрутов на основе истории пользователя.

    Оркестрация:
    1. Получить user_id по tg_id (через UserRepository)
    2. Получить все треки пользователя (через TrackFeaturesRepository)
    3. Вычислить средний вектор (через TrackVectorizer)
    4. Найти похожие треки (через TrackVectorIndex)
    5. Вернуть результат
    """

    def __init__(
        self,
        user_repo: UserRepository,
        features_repo: TrackFeaturesRepository,
        vectorizer: TrackVectorizer,
        vector_index: TrackVectorIndex,
    ):
        self.user_repo = user_repo
        self.features_repo = features_repo
        self.vectorizer = vectorizer
        self.vector_index = vector_index

    def execute(self, cmd: RecommendRoutesCommand) -> List[Dict[str, Any]]:
        """Возвращает список рекомендаций."""
        # 1. Получаем user_id по tg_id
        user_id = self.user_repo.get_id_by_tg_id(cmd.tg_id)
        if not user_id:
            return []

        # 2. Получаем все треки пользователя
        all_tracks = self.features_repo.get_all_by_user(user_id)
        if not all_tracks:
            return []

        # 3. Вычисляем средние значения признаков
        avg_features = self._compute_average(all_tracks)

        # 4. Векторизуем
        query_vector = self.vectorizer.vectorize(avg_features)

        # 5. Ищем похожие
        user_filter = None if cmd.include_other_users else user_id
        results = self.vector_index.search(query_vector=query_vector,top_k=cmd.top_k * 2,user_id_filter=user_filter)

        # 6. Фильтруем свои треки
        user_track_ids = {t["id"] for t in all_tracks}
        recommendations = []

        for r in results:
            if not cmd.include_other_users and r["track_id"] in user_track_ids:
                continue

            recommendations.append(r)
            if len(recommendations) >= cmd.top_k:
                break

        return recommendations

    @staticmethod
    def _compute_average(tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Вычисляет средние значения признаков."""
        if not tracks:
            return {}

        numeric_keys = [
            "total_distance_kilometers",
            "elevation_gain_per_kilometer",
            "path_sinuosity_ratio",
            "start_hour_of_day_utc",
            "day_of_week_index",
            "start_latitude_deg",
            "start_longitude_deg",
        ]

        avg = {}
        for key in numeric_keys:
            values = [t.get(key) for t in tracks if t.get(key) is not None]
            avg[key] = sum(values) / len(values) if values else None

        # Категориальные — самый частый
        route_cats = [t.get("route_curvature_category") for t in tracks if t.get("route_curvature_category")]
        terrain_cats = [t.get("terrain_category") for t in tracks if t.get("terrain_category")]

        avg["route_curvature_category"] = max(set(route_cats), key=route_cats.count) if route_cats else None
        avg["terrain_category"] = max(set(terrain_cats), key=terrain_cats.count) if terrain_cats else None

        return avg
