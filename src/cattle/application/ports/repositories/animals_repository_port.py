from abc import abstractmethod
from uuid import UUID

from src.cattle.application.ports.dtos.animal_dtos import AnimalCreateDTO, AnimalIdentifierDTO, AnimalUpdateDTO, AnimalsListQueryParamsDTO
from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.entities.animal_entity import AnimalEntity
from src.common.application.ports.repository import IRepository


class IAnimalsRepository(IRepository):
    @abstractmethod
    async def exists(self, identifier: UUID | AnimalIdentifierDTO) -> bool:
        raise NotImplemented

    @abstractmethod
    async def get_by_id(self, id: UUID, user_id: UUID) -> AnimalEntity | None:
        raise NotImplemented

    @abstractmethod
    async def get_by_caravana(self, caravana: str) -> AnimalEntity | None:
        raise NotImplemented

    @abstractmethod
    async def list_for_user(
        self,
        user_id: UUID,
        filters: AnimalsListQueryParamsDTO,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalEntity]:
        raise NotImplemented

    @abstractmethod
    async def create(self, data: AnimalCreateDTO) -> AnimalEntity:
        raise NotImplemented

    @abstractmethod
    async def update_data(self, id: UUID, data: AnimalUpdateDTO) -> AnimalEntity:
        raise NotImplemented

    @abstractmethod
    async def update_status(self, id: UUID, status: AnimalStatus) -> None:
        raise NotImplemented

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplemented
