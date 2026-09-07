from typing import Literal
from uuid import UUID

from src.market.domain.entities.sales import SaleEntity
from src.market.domain.repositories.sales import ISalesRepository
from src.market.domain.value_objects.sale_value_objects import SaleListQueryParamsValueObject

SaleOrderByField = Literal["sale_date", "price", "weight", "created_at"]


class ListSaleService:
    async def get_sales(
        self,
        filters: SaleListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: SaleOrderByField,
        repository: ISalesRepository,
        user_id: UUID | None = None,
    ) -> list[SaleEntity]:
        # user_id is passed through to the repository for future filtering
        return await repository.list_for_user(
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
            user_id=user_id,
        )
