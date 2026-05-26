from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.market.domain.entities.sales import SaleEntity
from src.market.domain.repositoriyes.sales import ISalesRepository
from src.market.domain.services.sale_services.get_sale_service import GetSaleService


class GetSaleCase:
    def __init__(self, uow: IUoW, service: GetSaleService):
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID, user_id: UUID) -> SaleEntity:
        async with self.uow as uow:
            repository = uow.get_repository(ISalesRepository)
            return await self.service.get_sale(
                id=id,
                user_id=user_id,
                repository=repository,
            )
