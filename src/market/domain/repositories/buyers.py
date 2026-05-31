from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository
from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.value_objects.buyer_value_objects import (
    BuyerCreateValueObject,
    BuyerListQueryParamsValueObject,
    BuyerUpdateValueObject,
)


class IBuyersRepository(IRepository):
    @abstractmethod
    async def exists(self, id: UUID, user_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self,
        id: UUID,
        user_id: UUID,
    ) -> BuyerEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list_for_user(
        self,
        user_id: UUID,
        filters: BuyerListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[BuyerEntity]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, data: BuyerCreateValueObject) -> BuyerEntity:
        raise NotImplementedError

    @abstractmethod
    async def update_data(
        self,
        id: UUID,
        user_id: UUID,
        data: BuyerUpdateValueObject,
    ) -> BuyerEntity:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplementedError
