from datetime import datetime
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tg_id: int = Field(index=True, unique=True)
    name: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)