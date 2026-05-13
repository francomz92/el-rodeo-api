from abc import abstractmethod
from uuid import UUID

from src.auth.domain.entities import UserEntity
from src.auth.domain.value_objects.user_value_object import (
    UserCreationValueObject,
    UserUpdateValueObject,
)
from src.common.domain.repository import IRepository


class IUserRepository(IRepository):
    @abstractmethod
    async def exists(self, dni: str, email: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID) -> UserEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_dni(self, dni: str) -> UserEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, data: UserCreationValueObject, password: str) -> UserEntity:
        raise NotImplementedError

    @abstractmethod
    async def update_data(self, id: UUID, data: UserUpdateValueObject) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_password(self, id: UUID, password: str) -> None:
        raise NotImplementedError
