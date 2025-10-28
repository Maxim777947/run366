from sqlmodel import Session, select
from app.domain.ports.user import UserRepository, UserEntity
from app.infrastructure.db.models.user_metadata import UserMetadata

class UserRepoSQL(UserRepository):
    def __init__(self, session: Session):
        self.session = session

    def upsert(self, user: UserEntity) -> int:
        """Создать или изменить данные пользователя"""

        row = self.session.exec(
            select(UserMetadata).where(UserMetadata.tg_id == user.tg_id)
        ).first()
        print(user)
        if row is None:
            row = UserMetadata(
                tg_id=user.tg_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                is_bot=user.is_bot,
                language_code=user.language_code,
                created_at=user.created_at,
            )
            self.session.add(row)
        else:
            row.username = user.username
            row.first_name = user.first_name
            row.last_name = user.last_name
            row.is_bot = user.is_bot
            row.language_code = user.language_code
            row.created_at = user.created_at

        self.session.commit()
        self.session.refresh(row)
        return row.id

    def get_by_id(self, user_id: int):
        row = self.session.get(UserMetadata, user_id)
        if not row:
            return None
        return UserEntity(**row.model_dump())
