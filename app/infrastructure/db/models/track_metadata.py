from sqlmodel import SQLModel, Field
from datetime import datetime


class TrackMetadata(SQLModel, table=True):
    """Модель трека"""

    id: str = Field(primary_key=True)
    user_id: int = Field(index=True, foreign_key="users.id")
    filename: str
    format: str
    source: str = "telegram"
    distance_km: float | None = None
    duration_s: int | None = None
    elevation_gain_m: float | None = None
    created_at: datetime

    __tablename__ = "tracks"
