"""Domain ports (interfaces) defining boundaries.

Responsibilities:
- Declare stable interfaces that the application depends upon.

Constraints:
- No imports from infrastructure or frameworks.
"""

from typing import Optional, Protocol

from app.domain.models.track import Track, TrackFormat


class TrackStorage(Protocol):
    def save_raw(self, track: Track, content: bytes) -> str: ...
    def exists(self, track_id: str) -> bool: ...


class TrackIdGenerator(Protocol):
    def new_id(self) -> str: ...


class TrackFormatDetector(Protocol):
    def detect(self, filename: str, first_bytes: bytes) -> Optional[TrackFormat]: ...


class TrackMetadataRepository(Protocol):
    def save(self, meta) -> None: ...


class TrackParser(Protocol):
    def parse(self, fmt: TrackFormat, blob: bytes) -> dict: ...
