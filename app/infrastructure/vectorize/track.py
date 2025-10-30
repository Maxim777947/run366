import math
from typing import Any, List, Mapping

from app.domain.ports.track import TrackVectorizer


class HandcraftedTrackVectorizer(TrackVectorizer):
    """
    Простая реализация векторизатора признаков трека.
    Вектор фиксированной длины 13, все названия полные.
    """

    def vector_size(self) -> int:
        return 13

    def vectorize(self, features: Mapping[str, Any]) -> List[float]:
        def normalize_to_unit_interval(value: Any, min_value: float, max_value: float) -> float:
            if value is None:
                return 0.0
            as_float = float(value)
            clipped = max(min_value, min(max_value, as_float))
            return (clipped - min_value) / (max_value - min_value + 1e-9)

        normalized_total_distance_kilometers = normalize_to_unit_interval(
            features.get("total_distance_kilometers"), 0.0, 30.0
        )
        normalized_elevation_gain_per_kilometer = normalize_to_unit_interval(
            features.get("elevation_gain_per_kilometer"), 0.0, 60.0
        )
        normalized_path_sinuosity_ratio = normalize_to_unit_interval(features.get("path_sinuosity_ratio"), 1.0, 3.0)

        start_hour_of_day_utc = features.get("start_hour_of_day_utc") or 0
        hour_angle_radians = 2.0 * math.pi * (start_hour_of_day_utc / 24.0)
        start_hour_of_day_sin = math.sin(hour_angle_radians)
        start_hour_of_day_cos = math.cos(hour_angle_radians)

        day_of_week_index = features.get("day_of_week_index") or 0
        day_angle_radians = 2.0 * math.pi * (day_of_week_index / 7.0)
        day_of_week_sin = math.sin(day_angle_radians)
        day_of_week_cos = math.cos(day_angle_radians)

        start_latitude_deg = float(features.get("start_latitude_deg") or 0.0)
        start_longitude_deg = float(features.get("start_longitude_deg") or 0.0)
        start_latitude_radians = math.radians(start_latitude_deg)
        start_longitude_radians = math.radians(start_longitude_deg)
        start_latitude_sin = math.sin(start_latitude_radians)
        start_latitude_cos = math.cos(start_latitude_radians)
        start_longitude_sin = math.sin(start_longitude_radians)
        start_longitude_cos = math.cos(start_longitude_radians)

        route_curvature_category = features.get("route_curvature_category")
        terrain_category = features.get("terrain_category")
        route_curvature_scalar = {"straight": 0.0, "mixed": 0.5, "curvy": 1.0}.get(route_curvature_category, 0.5)
        terrain_category_scalar = {"flat": 0.0, "rolling": 0.5, "hilly": 1.0}.get(terrain_category, 0.5)

        return [
            normalized_total_distance_kilometers,
            normalized_elevation_gain_per_kilometer,
            normalized_path_sinuosity_ratio,
            start_hour_of_day_sin,
            start_hour_of_day_cos,
            day_of_week_sin,
            day_of_week_cos,
            start_latitude_sin,
            start_latitude_cos,
            start_longitude_sin,
            start_longitude_cos,
            route_curvature_scalar,
            terrain_category_scalar,
        ]
