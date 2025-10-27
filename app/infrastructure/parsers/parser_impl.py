"""Infrastructure parser implementation of TrackParser port.

Dispatches by TrackFormat and delegates to concrete parsers.
"""

from app.domain.ports import TrackParser
from app.domain.track import TrackFormat
from .gpx_parser import parse_gpx


class TrackParserImpl(TrackParser):
    def parse(self, fmt: TrackFormat, blob: bytes) -> dict:
        if fmt == TrackFormat.GPX:
            return parse_gpx(blob)
        # elif fmt == TrackFormat.FIT: ...
        # elif fmt == TrackFormat.TCX: ...
        return {}
