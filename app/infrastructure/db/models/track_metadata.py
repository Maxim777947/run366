from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class TrackMetadata(SQLModel, table=True):
    """Модель трека"""

    __tablename__ = "tracks"
    id: str = Field(primary_key=True)
    user_id: int = Field(index=True, foreign_key="users.id")
    filename: str
    format: str
    source: str = "telegram"
    distance_km: float | None = None
    duration_s: int | None = None
    elevation_gain_m: float | None = None
    created_at: datetime
    features: Optional["TrackFeaturesMetadata"] = Relationship(
        back_populates="track",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )


class TrackFeaturesMetadata(SQLModel, table=True):
    __tablename__ = "track_features"

    id: str = Field(primary_key=True, foreign_key="tracks.id")
    track: "TrackMetadata" = Relationship(back_populates="features")

    # Время старта/финиша в UTC
    start_datetime_utc: datetime | None = None  # дата/время старта (UTC)
    end_datetime_utc: datetime | None = None  # дата/время финиша (UTC)

    # Удобные признаки времени
    start_hour_of_day_utc: int | None = Field(
        default=None, index=True
    )  # час старта 0..23 (UTC)
    day_of_week_index: int | None = Field(
        default=None, index=True
    )  # день недели 0=Пн .. 6=Вс

    # Геопозиция старта/финиша
    start_latitude_deg: float | None = None  # широта старта, градусы
    start_longitude_deg: float | None = None  # долгота старта, градусы
    end_latitude_deg: float | None = None  # широта финиша, градусы
    end_longitude_deg: float | None = None  # долгота финиша, градусы

    # Приближённый идентификатор зоны старта (округление координат)
    start_area_identifier_approx: str | None = Field(default=None, index=True)

    # Дистанция
    total_distance_kilometers: float | None = None  # суммарная дистанция, км
    straight_line_distance_kilometers: float | None = (
        None  # расстояние по прямой старт→финиш, км
    )

    # Извилистость траектории
    path_sinuosity_ratio: float | None = None  # отношение дистанции к прямой
    route_curvature_category: str | None = Field(
        default=None, index=True
    )  # straight/mixed/curvy

    # Рельеф
    total_elevation_gain_meters: float | None = None  # суммарный набор высоты, м
    total_elevation_loss_meters: float | None = None  # суммарный сброс высоты, м
    elevation_gain_per_kilometer: float | None = None  # набор на каждый км, м/км
    terrain_category: str | None = Field(default=None, index=True)  # flat/rolling/hilly

    # Временные метрики
    total_elapsed_duration_seconds: int | None = (
        None  # полная длительность (старт→финиш), сек
    )
    total_moving_duration_seconds: int | None = None  # время в движении, сек
    total_stopped_duration_seconds: int | None = None  # время остановок, сек

    # Скорости
    average_speed_kilometers_per_hour: float | None = (
        None  # средняя скорость (движение), км/ч
    )
    maximum_speed_kilometers_per_hour: float | None = (
        None  # максимальная скорость, км/ч
    )

    # Служебные поля
    features_version: int = 1  # версия расчёта фич
    computed_at_utc: datetime = Field(
        default_factory=datetime.utcnow
    )  # когда посчитали фичи (UTC)
    source_format: str | None = "gpx"  # исходный формат файла
