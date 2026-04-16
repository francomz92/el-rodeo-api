from abc import abstractmethod
from uuid import UUID

from src.auth.application.ports.dtos.user_dtos import UserCreationDTO, UserUpdateDTO
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
    async def create(self, data: UserCreationDTO, password: str) -> UserEntity:
        raise NotImplemented

    @abstractmethod
    async def update_data(self, id: UUID, data: UserUpdateDTO) -> None:
        raise NotImplemented

    @abstractmethod
    async def update_password(self, id: UUID, password: str) -> None:
        raise NotImplemented
