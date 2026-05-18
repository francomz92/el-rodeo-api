from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository
from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity
from src.finance.domain.value_objetcts.animal_supplies_value_objects import (
    AnimalSuppliesCreateValueObject,
    AnimalSuppliesListQueryParamsValueObject,
    AnimalSuppliesUpdateValueObject,
)


class IAnimalSuppliesRepository(IRepository):
    @abstractmethod
    async def exists(self, id: UUID, user_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self,
        id: UUID,
        user_id: UUID,
    ) -> AnimalSupplyEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list_for_user(
        self,
        user_id: UUID,
        filters: AnimalSuppliesListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalSupplyEntity]:
        raise NotImplementedError

    @abstractmethod
    async def create(
        self,
        data: AnimalSuppliesCreateValueObject,
    ) -> AnimalSupplyEntity:
        raise NotImplementedError

    @abstractmethod
    async def update_data(
        self,
        id: UUID,
        user_id: UUID,
        data: AnimalSuppliesUpdateValueObject,
    ) -> AnimalSupplyEntity:
        raise NotImplementedError

    @abstractmethod
    async def incrase_stock(
        self,
        id: UUID,
        amount_to_incrase: float,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplementedError
