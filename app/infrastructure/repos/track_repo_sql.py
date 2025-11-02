import os
import uuid
from pathlib import Path
from typing import Optional

from sqlmodel import Session, select

from app.domain.models.track import Track, TrackFormat
from app.domain.ports.track import TrackFormatDetector, TrackIdGenerator, TrackStorage
from app.infrastructure.db.models.track_metadata import TrackFeaturesMetadata, TrackMetadata


class TrackMetadataRepoSQL:
    """Реализация репозитория метаданных через SQLModel (PostgreSQL)."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, meta: dict) -> None:
        row = TrackMetadata(**meta)
        self.session.add(row)
        self.session.commit()


class TrackFeaturesRepoSQL:
    def __init__(self, session: Session):
        self.session = session

    def upsert(self, features: dict) -> None:
        row = self.session.get(TrackFeaturesMetadata, features["id"])
        if row is None:
            row = TrackFeaturesMetadata(**features)
            self.session.add(row)
        else:
            for k, v in features.items():
                setattr(row, k, v)
        self.session.commit()


    def get_all_by_user(self, user_id: int) -> list[dict]:
        """Возвращает все треки пользователя."""

        stmt = select(TrackFeaturesMetadata).where(TrackFeaturesMetadata.user_id == user_id)
        rows = self.session.exec(stmt).all()

        return [
            {
                "id": row.id,
                "user_id": row.user_id,
                "total_distance_kilometers": row.total_distance_kilometers,
                "elevation_gain_per_kilometer": row.elevation_gain_per_kilometer,
                "path_sinuosity_ratio": row.path_sinuosity_ratio,
                "start_hour_of_day_utc": row.start_hour_of_day_utc,
                "day_of_week_index": row.day_of_week_index,
                "start_latitude_deg": row.start_latitude_deg,
                "start_longitude_deg": row.start_longitude_deg,
                "route_curvature_category": row.route_curvature_category,
                "terrain_category": row.terrain_category,
            }
            for row in rows
        ]


class UUIDGen(TrackIdGenerator):
    def new_id(self) -> str:
        return uuid.uuid4().hex


class LocalFSStorage(TrackStorage):
    """Хранилище треков на локальной файловой системе."""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)

    def save_raw(self, track: Track, content: bytes) -> str:
        user_dir = self.base_dir / str(track.user_id)
        track_dir = user_dir / track.id
        track_dir.mkdir(parents=True, exist_ok=True)
        file_path = track_dir / track.filename
        with open(file_path, "wb") as f:
            f.write(content)
        return str(file_path)

    def exists(self, track_id: str) -> bool:
        for p in self.base_dir.rglob("*"):
            if p.is_dir() and p.name == track_id:
                return True
        return False


class SimpleFormatDetector(TrackFormatDetector):
    def detect(self, filename: str, first_bytes: bytes) -> Optional[TrackFormat]:
        ext = os.path.splitext(filename)[1].lower().lstrip(".")
        if ext in {"gpx", "fit", "tcx"}:
            return TrackFormat(ext)
        return None
