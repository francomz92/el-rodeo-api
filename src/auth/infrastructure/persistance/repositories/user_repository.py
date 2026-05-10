from uuid import UUID

from sqlalchemy import exists, insert, select, update

from src.auth.domain.entities import UserEntity
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.auth.domain.value_objects.user_value_object import (
    UserCreationValueObject,
    UserUpdateValueObject,
)
from src.auth.infrastructure.persistance.models import User
from src.common.application.types import Sentinel
from src.common.infrastructure.persistence.repositories.mixins import SessionMixin


class UserRepository(IUserRepository, SessionMixin):
    async def exists(self, dni: str) -> bool:
        query = exists(User).where(User.dni == dni).select()
        result = await self.db.execute(query)
        return result.scalar_one()

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

    async def create(
        self,
        data: UserCreationValueObject,
        password: str,
    ) -> UserEntity:
        query = (
            insert(User)
            .values(
                **vars(data),
                password=password,
            )
            .returning(User.id)
        )
        result = await self.db.execute(query)
        user_id = result.scalar_one()
        return await self.get_by_id(user_id)  # type: ignore

    async def update_data(self, id: UUID, data: UserUpdateValueObject) -> None:
        kws = {k: v for k, v in vars(data).items() if v != Sentinel.UNSET}
        query = update(User).where(User.id == id).values(**kws)
        await self.db.execute(query)

    async def update_password(self, id: UUID, password: str) -> None:
        query = update(User).where(User.id == id).values(password=password)
        await self.db.execute(query)

    def _build_user(self, user_db: User) -> UserEntity:
        return UserEntity(
            id=user_db.id,
            name=user_db.name,
            dni=user_db.dni,
            created_at=user_db.created_at,
            is_admin=user_db.is_admin,
            _hashed_password=user_db.password,
        )
