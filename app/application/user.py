from datetime import datetime, timezone
from app.domain.ports.user import UserRepository, UserEntity


class UpsertTelegramUserUseCase:
    def __init__(self, users: UserRepository):
        self.users = users

    def execute(self, tg_user) -> int:
        return self.users.upsert(
            UserEntity(
                tg_id=tg_user.id,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                is_bot=tg_user.is_bot,
                language_code=tg_user.language_code,
                username=tg_user.username,
                created_at=datetime.now(timezone.utc),
            )
        )
