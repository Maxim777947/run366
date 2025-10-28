from typing import Protocol, Optional
from app.domain.models.users import UserEntity


class UserRepository(Protocol):
    def upsert(self, user: UserEntity) -> int: ...
    def get_by_id(self, user_id: int) -> Optional[UserEntity]: ...
