"""Infrastructure repository: SQL implementation of TrackMetadataRepository port.

Responsibilities:
- Map domain/application DTO to ORM row and persist via SQLModel/Session.

Constraints:
- Domain and application must not import this module directly; depend on the
  TrackMetadataRepository port from app.domain.ports and provide this
  implementation at the composition root (adapters/config).
"""

from sqlmodel import Session
from app.infrastructure.db.models.track_metadata import TrackMetadata


class TrackMetadataRepoSQL:
    """Реализация репозитория метаданных через SQLModel (PostgreSQL)."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, meta: dict) -> None:
        row = TrackMetadata(**meta)
        self.session.add(row)
        self.session.commit()
