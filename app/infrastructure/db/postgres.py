"""Infrastructure: SQLModel engine/session factory and DB init.

Constraints:
- Import ORM models locally inside init_db to avoid cross-layer cycles.
"""

from sqlmodel import SQLModel, create_engine, Session
from app.config import settings
from contextlib import contextmanager


from app.infrastructure.db.models.track_metadata import TrackMetadata
from app.infrastructure.db.models.user_metadata import UserMetadata


engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)


def init_db() -> None:
    pass


@contextmanager
def get_session():
    with Session(engine) as session:
        yield session
