from src.market.domain.entities.sales import SaleEntity
from src.market.domain.repositories.sales import ISalesRepository
from src.market.domain.value_objects.sale_value_objects import SaleListQueryParamsValueObject


class ListSaleService:
    async def get_sales(
        self,
        filters: SaleListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
        repository: ISalesRepository,
    ) -> list[SaleEntity]:
        return await repository.list_for_user(
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
