from collections import deque
from datetime import datetime, timezone
from math import atan2, cos, radians, sin, sqrt

import gpxpy


def parse_gpx(blob: bytes) -> dict:
    """Парсер для стандартных метрик"""
    g = gpxpy.parse(blob.decode("utf-8", errors="ignore"))
    total_m = 0.0
    total_s = 0
    gain = 0.0
    for tr in g.tracks:
        for seg in tr.segments:
            total_m += seg.length_2d() or 0.0
            if seg.points:
                st, en = seg.points[0].time, seg.points[-1].time
                if st and en:
                    total_s += int((en - st).total_seconds())
            prev = None
            for p in seg.points:
                # [trkpt:51.59814667,46.02006333@128.0@2025-10-24 13:58:23.044000+00:00]
                # 51.59814667 — широта (latitude)
                # 46.02006333 — долгота (longitude)
                # 128.0 — высота в метрах (elevation)
                # 2025-10-24 13:58:23.044000+00:00 — время в UTC (datetime)
                if p.elevation is not None:
                    if prev is not None and p.elevation > prev:
                        gain += p.elevation - prev
                    prev = p.elevation

    return {
        "distance_km": round(total_m / 1000, 3),
        "duration_s": total_s,
        "elevation_gain_m": round(gain, 1),
    }


def _haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def _haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def _elevation_gain_loss_gpx(g, min_delta_m=1.0, smooth_window=3, min_horiz_m=3.0):
    # min_delta_m: игнорировать перепады меньше порога (срезаем шум)
    # smooth_window: скользящее среднее высоты (сглаживание)
    # min_horiz_m: не считать соседние точки слишком близко (GPS-дребезг)
    gain = 0.0
    loss = 0.0
    for tr in g.tracks:
        for seg in tr.segments:
            prev_lat = prev_lon = None
            prev_elev_sm = None
            buf = deque(maxlen=smooth_window)
            for p in seg.points:
                if p.elevation is None or p.latitude is None or p.longitude is None:
                    continue
                # пропускаем слишком близкие по горизонтали точки
                if prev_lat is not None:
                    if _haversine_m(prev_lat, prev_lon, p.latitude, p.longitude) < min_horiz_m:
                        buf.append(p.elevation)
                        continue
                buf.append(p.elevation)
                elev_sm = sum(buf) / len(buf)
                if prev_elev_sm is not None:
                    delta = elev_sm - prev_elev_sm
                    if delta >= min_delta_m:
                        gain += delta
                    elif delta <= -min_delta_m:
                        loss += -delta
                prev_lat, prev_lon, prev_elev_sm = p.latitude, p.longitude, elev_sm
    return round(gain, 1), round(loss, 1)


def extract_track_features_from_gpx(blob: bytes) -> dict:
    """
    Возвращает словарь агрегированных фич для одного GPX‑трека.
    Все метки времени — в UTC.
    """
    g = gpxpy.parse(blob.decode("utf-8", errors="ignore"))

    # Базовые агрегаты
    total_distance_meters = g.length_2d() or 0.0
    moving_data = g.get_moving_data()  # данные о движении/стопах/макс. скорости
    uphill_downhill = g.get_uphill_downhill()  # (набор, сброс), м
    time_bounds = g.get_time_bounds()  # (start_time, end_time), UTC

    # Первая и последняя точки трека (для прямой линии старт→финиш)
    first_point = last_point = None
    for track in g.tracks:
        for seg in track.segments:
            if seg.points:
                if first_point is None:
                    first_point = seg.points[0]
                last_point = seg.points[-1]

    start_latitude_deg = start_longitude_deg = None
    end_latitude_deg = end_longitude_deg = None
    if first_point:
        start_latitude_deg = first_point.latitude
        start_longitude_deg = first_point.longitude
    if last_point:
        end_latitude_deg = last_point.latitude
        end_longitude_deg = last_point.longitude

    # Расстояние по прямой (старт→финиш)
    straight_line_distance_meters = 0.0
    if first_point and last_point:
        straight_line_distance_meters = _haversine_distance_meters(
            start_latitude_deg, start_longitude_deg, end_latitude_deg, end_longitude_deg
        )

    # Преобразования единиц
    total_distance_kilometers = round(total_distance_meters / 1000.0, 3)
    straight_line_distance_kilometers = round(straight_line_distance_meters / 1000.0, 3)

    # Время старта/финиша (UTC)
    start_datetime_utc = getattr(time_bounds, "start_time", None) if time_bounds else None
    end_datetime_utc = getattr(time_bounds, "end_time", None) if time_bounds else None

    # Производные метрики
    eps = 1e-6
    path_sinuosity_ratio = (
        (total_distance_kilometers / max(straight_line_distance_kilometers, eps))
        if total_distance_kilometers and straight_line_distance_kilometers
        else None
    )

    total_elevation_gain_meters, total_elevation_loss_meters = _elevation_gain_loss_gpx(g)

    elevation_gain_per_kilometer = (
        total_elevation_gain_meters / max(total_distance_kilometers, eps) if total_distance_kilometers else None
    )

    total_elapsed_duration_seconds = (
        int((end_datetime_utc - start_datetime_utc).total_seconds())
        if (start_datetime_utc and end_datetime_utc)
        else None
    )

    total_moving_duration_seconds = int(moving_data.moving_time) if moving_data else None
    total_stopped_duration_seconds = int(moving_data.stopped_time) if moving_data else None
    average_speed_kilometers_per_hour = (
        round((moving_data.moving_distance / moving_data.moving_time) * 3.6, 2)
        if (moving_data and moving_data.moving_time)
        else None
    )
    maximum_speed_kilometers_per_hour = (
        round(moving_data.max_speed * 3.6, 2) if (moving_data and moving_data.max_speed) else None
    )

    # Категория извилистости маршрута
    if path_sinuosity_ratio is None:
        route_curvature_category = None
    elif path_sinuosity_ratio < 1.05:
        route_curvature_category = "straight"  # преимущественно прямая
    elif path_sinuosity_ratio > 1.15:
        route_curvature_category = "curvy"  # извилистая
    else:
        route_curvature_category = "mixed"  # смешанная

    # Категория рельефа по набору/км
    if elevation_gain_per_kilometer is None:
        terrain_category = None
    elif elevation_gain_per_kilometer < 10:
        terrain_category = "flat"  # равнина (< 10 м/км)
    elif elevation_gain_per_kilometer > 30:
        terrain_category = "hilly"  # холмы/горы (> 30 м/км)
    else:
        terrain_category = "rolling"  # волнистый рельеф (10–30 м/км)

    # Приближённая “зона старта” (округление координат)
    def _approx_start_area_id(lat, lon, precision=3):
        if lat is None or lon is None:
            return None
        return f"{round(lat, precision)}:{round(lon, precision)}"

    start_area_identifier_approx = _approx_start_area_id(start_latitude_deg, start_longitude_deg, precision=3)

    start_hour_of_day_utc = start_datetime_utc.hour if start_datetime_utc else None
    day_of_week_index = start_datetime_utc.weekday() if start_datetime_utc else None

    return {
        "start_datetime_utc": start_datetime_utc,
        "end_datetime_utc": end_datetime_utc,
        "start_hour_of_day_utc": start_hour_of_day_utc,
        "day_of_week_index": day_of_week_index,
        "start_latitude_deg": start_latitude_deg,
        "start_longitude_deg": start_longitude_deg,
        "end_latitude_deg": end_latitude_deg,
        "end_longitude_deg": end_longitude_deg,
        "start_area_identifier_approx": start_area_identifier_approx,
        "total_distance_kilometers": total_distance_kilometers,
        "straight_line_distance_kilometers": straight_line_distance_kilometers,
        "path_sinuosity_ratio": round(path_sinuosity_ratio, 3) if path_sinuosity_ratio is not None else None,
        "route_curvature_category": route_curvature_category,
        "total_elevation_gain_meters": round(total_elevation_gain_meters, 1),
        "total_elevation_loss_meters": round(total_elevation_loss_meters, 1),
        "elevation_gain_per_kilometer": (
            round(elevation_gain_per_kilometer, 1) if elevation_gain_per_kilometer is not None else None
        ),
        "terrain_category": terrain_category,
        "total_elapsed_duration_seconds": total_elapsed_duration_seconds,
        "total_moving_duration_seconds": total_moving_duration_seconds,
        "total_stopped_duration_seconds": total_stopped_duration_seconds,
        "average_speed_kilometers_per_hour": average_speed_kilometers_per_hour,
        "maximum_speed_kilometers_per_hour": maximum_speed_kilometers_per_hour,
        "features_version": 1,
        "computed_at_utc": datetime.now(timezone.utc),
        "source_format": "gpx",
    }
