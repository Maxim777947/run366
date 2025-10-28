"""Infrastructure parser implementation of TrackParser port.

Dispatches by TrackFormat and delegates to concrete parsers.
"""

from typing import Any, Mapping

from app.domain.models.track import TrackFormat
from app.domain.ports.track import TrackFeatureExtractor, TrackParser

from .gpx_parser import extract_track_features_from_gpx, parse_gpx


class TrackParserImpl(TrackParser):
    def parse(self, fmt: TrackFormat, blob: bytes) -> dict:
        if fmt == TrackFormat.GPX:
            return parse_gpx(blob)
        return {}


class TrackFeatureExtractorImpl(TrackFeatureExtractor):
    def extract(self, fmt: TrackFormat, blob: bytes) -> Mapping[str, Any]:
        if fmt == TrackFormat.GPX:
            return extract_track_features_from_gpx(blob)
        return {}
