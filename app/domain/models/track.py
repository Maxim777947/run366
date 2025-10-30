"""Domain entities.

Constraints:
- Do not import SQLModel/ORM/DB clients/frameworks.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Optional


class TrackFormat(StrEnum):
    GPX = "gpx"
    FIT = "fit"
    TCX = "tcx"


@dataclass(frozen=True)
class Track:
    """Базовая доменная сущность трека."""

    id: str
    user_id: int
    filename: str
    format: TrackFormat
    source: Optional[str]
    created_at: datetime


@dataclass(frozen=True)
class TrackFeatures:
    """Базовая доменная сущность для основных метрик трека"""

    id: str
    # Время (UTC)
    start_datetime_utc: Optional[datetime]
    end_datetime_utc: Optional[datetime]
    start_hour_of_day_utc: Optional[int]
    day_of_week_index: Optional[int]

    # Геопозиция старта/финиша
    start_latitude_deg: Optional[float]
    start_longitude_deg: Optional[float]
    end_latitude_deg: Optional[float]
    end_longitude_deg: Optional[float]
    start_area_identifier_approx: Optional[str]
    # Дистанции/извилистость
    total_distance_kilometers: Optional[float]
    straight_line_distance_kilometers: Optional[float]
    path_sinuosity_ratio: Optional[float]
    route_curvature_category: Optional[str]

    # Рельеф
    total_elevation_gain_meters: Optional[float]
    total_elevation_loss_meters: Optional[float]
    elevation_gain_per_kilometer: Optional[float]
    terrain_category: Optional[str]

    # Время/скорость
    total_elapsed_duration_seconds: Optional[int]
    total_moving_duration_seconds: Optional[int]
    total_stopped_duration_seconds: Optional[int]
    average_speed_kilometers_per_hour: Optional[float]
    maximum_speed_kilometers_per_hour: Optional[float]

    # Служебные
    features_version: int
    computed_at_utc: datetime
    source_format: Optional[str]


@dataclass(frozen=True)
class ComputeAndIndexTrackFeaturesCommand:
    """
    Входные данные сценария: идентификаторы, формат и бинарное содержимое трека.
    """

    track_id: str
    track_format: TrackFormat
    file_bytes: bytes
