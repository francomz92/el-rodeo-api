from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository
from src.finance.domain.entities.animal_supplies import SupplyTypeEntinty
from src.finance.domain.value_objetcts.animal_supply_type_value_objects import (
    AnimalSupplyTypeCreateValueObject,
    AnimalSupplyTypeListQueryParamsValueObject,
    AnimalSupplyTypeUpdateValueObject,
)


class ISupplyTypesRepository(IRepository):
    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID) -> SupplyTypeEntinty | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_name(self, name: str) -> SupplyTypeEntinty | None:
        raise NotImplementedError

    @abstractmethod
    async def list(
        self,
        filters: AnimalSupplyTypeListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[SupplyTypeEntinty]:
        raise NotImplementedError

    @abstractmethod
    async def create(
        self,
        data: AnimalSupplyTypeCreateValueObject,
    ) -> SupplyTypeEntinty:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        id: UUID,
        data: AnimalSupplyTypeUpdateValueObject,
    ) -> SupplyTypeEntinty:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplementedError
