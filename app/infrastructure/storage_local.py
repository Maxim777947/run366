import os
from pathlib import Path
from app.domain.ports import TrackStorage
from app.domain.track import Track


class LocalFSStorage(TrackStorage):
    """Хранилище треков на локальной файловой системе."""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)

    def save_raw(self, track: Track, content: bytes) -> str:
        user_dir = self.base_dir / str(track.user_id)
        track_dir = user_dir / track.id
        track_dir.mkdir(parents=True, exist_ok=True)
        file_path = track_dir / track.filename
        with open(file_path, "wb") as f:
            f.write(content)
        return str(file_path)

    def exists(self, track_id: str) -> bool:
        return any(self.base_dir.rglob(f"{track_id}"))
