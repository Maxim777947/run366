from sqlmodel import Session
from app.infrastructure.db.models.track_metadata import TrackMetadata as TM


class TrackMetadataRepoSQL:
    """Реализация репозитория метаданных через SQLModel (PostgreSQL)."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, meta: dict) -> None:
        row = TM(**meta)
        self.session.add(meta)
        self.session.commit()
