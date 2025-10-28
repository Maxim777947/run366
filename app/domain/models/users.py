from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class UserEntity:
    tg_id: int
    first_name: str
    last_name: str
    is_bot: bool
    language_code: str
    username: str
    created_at: datetime
    id: Optional[int] = None
