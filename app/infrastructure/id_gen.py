"""Infrastructure ID generator implementation of TrackIdGenerator port."""

import uuid
from app.domain.ports.track import TrackIdGenerator


class UUIDGen(TrackIdGenerator):
    def new_id(self) -> str:
        return uuid.uuid4().hex
