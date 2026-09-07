from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.market.domain.repositories.sales import ISalesRepository
from src.market.domain.services.sale_services.delete_sale_service import DeleteSaleService


class DeleteSaleCase:
    def __init__(self, uow: IUoW, service: DeleteSaleService):
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID) -> None:
        async with self.uow as uow:
            repository = uow.get_repository(ISalesRepository)
            await self.service.delete_sale(id, repository)
            await uow.commit()
