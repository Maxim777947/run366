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
    user_id: int = Field(index=True, foreign_key="users.id")
    track: "TrackMetadata" = Relationship(back_populates="features")
    start_datetime_utc: datetime | None = None
    end_datetime_utc: datetime | None = None
    start_hour_of_day_utc: int | None = Field(default=None, index=True)
    day_of_week_index: int | None = Field(default=None, index=True)
    start_latitude_deg: float | None = None
    start_longitude_deg: float | None = None
    end_latitude_deg: float | None = None
    end_longitude_deg: float | None = None
    start_area_identifier_approx: str | None = Field(default=None, index=True)
    total_distance_kilometers: float | None = None
    straight_line_distance_kilometers: float | None = None
    path_sinuosity_ratio: float | None = None
    route_curvature_category: str | None = Field(default=None, index=True)
    total_elevation_gain_meters: float | None = None
    total_elevation_loss_meters: float | None = None
    elevation_gain_per_kilometer: float | None = None
    terrain_category: str | None = Field(default=None, index=True)
    total_elapsed_duration_seconds: int | None = None
    total_moving_duration_seconds: int | None = None
    total_stopped_duration_seconds: int | None = None

    average_speed_kilometers_per_hour: float | None = None
    maximum_speed_kilometers_per_hour: float | None = None

    # Служебные поля
    features_version: int = 1
    computed_at_utc: datetime = Field(default_factory=datetime.utcnow)
    source_format: str | None = "gpx"
