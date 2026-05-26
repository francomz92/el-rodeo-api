from abc import abstractmethod
from uuid import UUID

from src.cattle.domain.entities.animal_entity import AnimalTypeEntinty
from src.cattle.domain.value_objects.animal_type_value_object import (
    AnimalTypeCreateValueObject,
    AnimalTypeListQueryParamsValueObject,
    AnimalTypeUpdateValueObject,
)
from src.common.domain.repository import IRepository


class IAnimalTypesRepository(IRepository):
    @abstractmethod
    async def get_by_id(self, id: UUID) -> AnimalTypeEntinty | None:
        raise NotImplementedError

    @abstractmethod
    async def list(
        self,
        filters: AnimalTypeListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalTypeEntinty]:
        raise NotImplementedError

    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def create(
        self,
        data: AnimalTypeCreateValueObject,
    ) -> AnimalTypeEntinty:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        id: UUID,
        data: AnimalTypeUpdateValueObject,
    ) -> AnimalTypeEntinty:
        raise NotImplementedError
