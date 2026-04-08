from uuid import UUID
from sqlalchemy import select, insert

from src.auth.application.ports.repositories.users import IUserRepository
from src.auth.domain.entities import UserEntity
from src.auth.domain.entities.users import UserEntity
from src.auth.infrastructure.persistance.models import User
from src.common.infrastructure.persistence.connections.db import AsyncSession


class UserRepository(IUserRepository):
    def __int__(self, db: AsyncSession):
        self.db = db

    def _build_user(self, user_db: User) -> UserEntity:
        return UserEntity(
            id=user_db.id,
            dni=user_db.dni,
            created_at=user_db.created_at,
            is_admin=user_db.is_admin,
            _hashed_password=user_db.password,
        )

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

    async def create(self, dni: str, hashed_password: str) -> UserEntity:
        query = insert(User).values(dni=dni, password=hashed_password)
        result = await self.db.execute(query)
        user_db = result.scalar_one()
        return self._build_user(user_db)
