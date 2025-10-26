from app.domain.ports import (
    TrackStorage,
    TrackIdGenerator,
    TrackFormatDetector,
    TrackMetadataRepository,
    TrackParser,
)
from app.domain.track import Track
from app.infrastructure.db.models.track_metadata import TrackMetadata
from datetime import datetime


class IngestTrackCommand:
    def __init__(
        self, user_id: int, filename: str, blob: bytes, source: str = "telegram"
    ):
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
    ):
        self.storage = storage
        self.id_gen = id_gen
        self.detector = detector
        self.parser = parser
        self.meta_repo = meta_repo

    def execute(self, cmd: IngestTrackCommand) -> TrackMetadata:
        fmt = self.detector.detect(cmd.filename, cmd.blob[:512])
        if not fmt:
            raise ValueError("Ожидаю GPX/FIT/TCX")

        track = Track(
            id=self.id_gen.new_id(),
            user_id=cmd.user_id,
            filename=cmd.filename,
            format=fmt,
            source=cmd.source,
            created_at=datetime.utcnow(),
        )

        self.storage.save_raw(track, cmd.blob)
        meta = self.parser.parse(fmt, cmd.blob) or {}

        row = TrackMetadata(
            id=track.id,
            user_id=track.user_id,
            filename=track.filename,
            format=track.format.value,
            source=track.source,
            created_at=track.created_at,
            distance_km=meta.get("distance_km"),
            duration_s=meta.get("duration_s"),
            elevation_gain_m=meta.get("elevation_gain_m"),
        )
        self.meta_repo.save(row)  # запись в БД
        return row
