"""Infrastructure format detector implementation of TrackFormatDetector port."""

import os
from typing import Optional
from app.domain.ports import TrackFormatDetector
from app.domain.track import TrackFormat


class SimpleFormatDetector(TrackFormatDetector):
    def detect(self, filename: str, first_bytes: bytes) -> Optional[TrackFormat]:
        ext = os.path.splitext(filename)[1].lower().lstrip(".")
        if ext in {"gpx", "fit", "tcx"}:
            return TrackFormat(ext)
        return None
