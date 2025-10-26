from sqlmodel import Session
from app.infrastructure.db.models.track_metadata import TrackMetadata


class TrackMetadataRepoSQL:
    """Реализация репозитория метаданных через SQLModel (PostgreSQL)."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, meta: TrackMetadata) -> None:
        self.session.add(meta)
        self.session.commit()
