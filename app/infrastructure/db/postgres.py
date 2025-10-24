from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

def init_db() -> None:
    # для MVP можно авто-создавать таблицы; в проде — alembic миграции
    from app.domian.models.users import User  # noqa
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session