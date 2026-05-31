from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.market.domain.entities.sales import SaleEntity
from src.market.domain.repositories.sales import ISalesRepository
from src.market.domain.services.sale_services.list_sale_service import ListSaleService
from src.market.domain.value_objects.sale_value_objects import SaleListQueryParamsValueObject


class ListSaleCase:
    def __init__(self, uow: IUoW, service: ListSaleService):
        self.uow = uow
        self.service = service

    async def execute(
        self,
        user_id: UUID,
        filters: SaleListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[SaleEntity]:
        async with self.uow as uow:
            repository = uow.get_repository(ISalesRepository)
            return await self.service.get_sales(
                user_id=user_id,
                filters=filters,
                limit=limit,
                offset=offset,
                order_by=order_by,
                repository=repository,
            )
