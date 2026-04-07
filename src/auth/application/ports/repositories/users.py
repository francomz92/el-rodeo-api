from abc import abstractmethod
from uuid import UUID

from src.common.application.ports.repository import IRepository
from src.auth.domain.entities import UserEntity


class IUserRepository(IRepository):
    @abstractmethod
    async def get_by_id(self, id: UUID) -> UserEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_dni(self, dni: str) -> UserEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, dni: str, hashed_password: str) -> UserEntity:
        raise NotImplemented
