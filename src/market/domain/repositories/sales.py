from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository
from src.market.domain.entities.sales import SaleEntity
from src.market.domain.value_objects.sale_value_objects import (
    SaleCreateValueObject,
    SaleListQueryParamsValueObject,
    SaleUpdateValueObject,
)


class ISalesRepository(IRepository):
    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self,
        id: UUID,
    ) -> SaleEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list_for_user(
        self,
        filters: SaleListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
        user_id: UUID | None = None,
    ) -> list[SaleEntity]:
        # NOTE: user_id is accepted for API/documentation purposes.
        #       The infra implementation may not enforce it as a filter yet.
        raise NotImplementedError

    @abstractmethod
    async def create(self, data: SaleCreateValueObject) -> SaleEntity:
        raise NotImplementedError

    @abstractmethod
    async def update_data(
        self,
        id: UUID,
        data: SaleUpdateValueObject,
    ) -> SaleEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        raise NotImplementedError
