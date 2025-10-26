# Доменная сущность
# Здесь нельзя импортировать SQLModel/ORM/клиенты БД/фреймворки.

from datetime import datetime

from enum import StrEnum
from dataclasses import dataclass
from typing import Optional


class TrackFormat(StrEnum):
    GPX = "gpx"
    FIT = "fit"
    TCX = "tcx"


@dataclass(frozen=True)
class Track:
    """Базовая доменная сущность трека (не зависит от БД и инфраструктуры)."""

    id: str
    user_id: int
    filename: str
    format: TrackFormat
    source: Optional[str]
    created_at: datetime
