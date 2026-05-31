from uuid import UUID

from src.market.domain.entities.sales import SaleEntity
from src.market.domain.repositories.sales import ISalesRepository
from src.market.domain.value_objects.sale_value_objects import SaleListQueryParamsValueObject


class ListSaleService:
    async def get_sales(
        self,
        user_id: UUID,
        filters: SaleListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
        repository: ISalesRepository,
    ) -> list[SaleEntity]:
        return await repository.list_for_user(
            user_id=user_id,
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
