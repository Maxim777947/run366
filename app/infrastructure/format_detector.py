"""Infrastructure format detector implementation of TrackFormatDetector port."""

import os
from typing import Optional

from app.domain.models.track import TrackFormat
from app.domain.ports.track import TrackFormatDetector


class SimpleFormatDetector(TrackFormatDetector):
    def detect(self, filename: str, first_bytes: bytes) -> Optional[TrackFormat]:
        ext = os.path.splitext(filename)[1].lower().lstrip(".")
        if ext in {"gpx", "fit", "tcx"}:
            return TrackFormat(ext)
        return None
