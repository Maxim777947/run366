"""Infrastructure: SQLModel engine/session factory and DB init.

Constraints:
- Import ORM models locally inside init_db to avoid cross-layer cycles.
"""

from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings
from app.infrastructure.db.models.track_metadata import TrackMetadata
from app.infrastructure.db.models.user_metadata import UserMetadata

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)


def init_db() -> None:
    pass


@contextmanager
def get_session():
    with Session(engine) as session:
        yield session
