"""Infrastructure: SQLModel engine/session factory and DB init.

Constraints:
- Import ORM models locally inside init_db to avoid cross-layer cycles.
"""

from sqlmodel import SQLModel, create_engine, Session
from app.config import settings
from contextlib import contextmanager


engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)


def init_db() -> None:
    from app.infrastructure.db.models import track_metadata, users

    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    with Session(engine) as session:
        yield session
