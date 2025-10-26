import gpxpy


def parse_gpx(blob: bytes) -> dict:
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
                if p.elevation is not None:
                    if prev is not None and p.elevation > prev:
                        gain += p.elevation - prev
                    prev = p.elevation

    return {
        "distance_km": round(total_m / 1000, 3),
        "duration_s": total_s,
        "elevation_gain_m": round(gain, 1),
    }
