from abc import abstractmethod
from uuid import UUID

from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.entities.animal_entity import AnimalEntity
from src.cattle.domain.value_objects.animal_value_objenct import (
    AnimalCreateValueObject,
    AnimalsListQueryParamsValueObject,
    AnimalUpdateValueObject,
)
from src.common.domain.repository import IRepository


class IAnimalsRepository(IRepository):
    @abstractmethod
    async def exists(
        self,
        id: UUID | None = None,
        user_id: UUID | None = None,
        type_id: UUID | None = None,
        caravana: str | None = None,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID, user_id: UUID) -> AnimalEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_caravana(self, caravana: str) -> AnimalEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list_for_user(
        self,
        user_id: UUID,
        filters: AnimalsListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalEntity]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, data: AnimalCreateValueObject) -> AnimalEntity:
        raise NotImplementedError

    @abstractmethod
    async def update_data(self, id: UUID, data: AnimalUpdateValueObject) -> AnimalEntity:
        raise NotImplementedError

    @abstractmethod
    async def update_status(self, id: UUID, status: AnimalStatus) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplementedError
