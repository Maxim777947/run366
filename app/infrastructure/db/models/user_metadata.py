from datetime import datetime
from sqlmodel import SQLModel, Field


class UserMetadata(SQLModel, table=True):
    """Модель пользователя"""

    id: int | None = Field(default=None, primary_key=True)
    tg_id: int = Field(index=True, unique=True)
    username: str = Field(unique=True)
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None
    is_bot: bool | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    __tablename__ = "users"
