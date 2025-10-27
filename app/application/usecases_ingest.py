"""Application layer use case: orchestrates steps of business logic.

Responsibilities:
- Coordinate domain and ports to perform a use case.
- No knowledge of technical details of persistence, network, or frameworks.

Constraints:
- Do not import or depend on ORM/SQL/HTTP/Telegram SDKs or any frameworks.
- Depend only on domain entities and ports (protocols) defined in app.domain.
"""

from datetime import datetime, timezone
from typing import Mapping, Any

from app.domain.ports import (
    TrackStorage,
    TrackIdGenerator,
    TrackFormatDetector,
    TrackMetadataRepository,
    TrackParser,
)
from app.domain.models.track import Track


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

    def execute(self, cmd: IngestTrackCommand) -> Mapping[str, Any]:
        fmt = self.detector.detect(cmd.filename, cmd.blob[:512])
        if not fmt:
            raise ValueError("Ожидаю GPX/FIT/TCX")

        track = Track(
            id=self.id_gen.new_id(),
            user_id=cmd.user_id,
            filename=cmd.filename,
            format=fmt,
            source=cmd.source,
            created_at=datetime.now(timezone.utc),
        )

        # 1) сохраняем сырой файл
        self.storage.save_raw(track, cmd.blob)

        # 2) парсим (инфраструктурой)
        meta = self.parser.parse(fmt, cmd.blob) or {}

        # 3) готовим DTO для БД (без ORM)
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

        # 5) возвращаем DTO (или track.id)
        return row
