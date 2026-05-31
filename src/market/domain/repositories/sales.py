from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository
from src.market.domain.entities.sales import SaleEntity
from src.market.domain.value_objects.sale_value_objects import (
    SaleCreateValueObject,
    SaleListQueryParamsValueObject,
)


class ISalesRepository(IRepository):
    @abstractmethod
    async def exists(self, id: UUID, user_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self,
        id: UUID,
        user_id: UUID,
    ) -> SaleEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list_for_user(
        self,
        user_id: UUID,
        filters: SaleListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[SaleEntity]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, data: SaleCreateValueObject) -> SaleEntity:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplementedError
