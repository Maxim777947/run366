from app.domain.ports import TrackParser
from app.domain.models.track import TrackFormat
from .gpx_parser import parse_gpx


class TrackParserImpl(TrackParser):
    def parse(self, fmt: TrackFormat, blob: bytes) -> dict:
        if fmt == TrackFormat.GPX:
            return parse_gpx(blob)
        return {}
