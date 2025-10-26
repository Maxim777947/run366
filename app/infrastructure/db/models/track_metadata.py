# Здесь храним ORM модели
# Здесь нельзя импортировать доменные сущности (чтобы не было циклов «домен ↔ инфраструктура»).

from sqlmodel import SQLModel, Field
from datetime import datetime


class TrackMetadata(SQLModel, table=True):
    id: str = Field(primary_key=True)
    user_id: int
    filename: str
    format: str
    source: str = "telegram"
    distance_km: float | None = None
    duration_s: int | None = None
    elevation_gain_m: float | None = None
    created_at: datetime
