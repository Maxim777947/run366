"""Domain must not contain ORM models.

This placeholder makes it explicit that ORM models live in
`app.infrastructure.db.models`. If a domain-level user entity is needed,
define it here as a dataclass without any framework/ORM dependencies.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class User:
    id: Optional[int]
    tg_id: int
    name: Optional[str]
    created_at: datetime
