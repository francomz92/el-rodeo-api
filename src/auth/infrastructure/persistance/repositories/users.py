from uuid import UUID
from sqlalchemy import select

from src.auth.application.ports.repositories.users import IUserRepository
from src.auth.domain.entities import UserEntity
from src.auth.domain.entities.users import UserEntity
from src.auth.infrastructure.persistance.models import User
from src.common.infrastructure.persistence.connections.db import AsyncSession


class UserRepository(IUserRepository):
    def __int__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: UUID) -> UserEntity | None:
        query = select(User).where(User.id == id)
        result = await self.db.execute(query)
        user_db = result.scalar_one_or_none()
        return self._build_user(user_db) if user_db else None

    async def get_by_dni(self, dni: str) -> UserEntity | None:
        query = select(User).where(User.dni == dni)
        result = await self.db.execute(query)
        user_db = result.scalar_one_or_none()
        return self._build_user(user_db) if user_db else None

    def _build_user(self, user_db: User):
        return UserEntity(
            id=user_db.id,
            dni=user_db.dni,
            created_at=user_db.created_at,
        )
