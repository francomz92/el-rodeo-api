from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.market.domain.entities.sales import SaleEntity
from src.market.domain.repositories.sales import ISalesRepository
from src.market.domain.services.sale_services.update_sale_service import UpdateSaleService
from src.market.domain.value_objects.sale_value_objects import SaleUpdateValueObject


class UpdateSaleCase:
    def __init__(self, uow: IUoW, service: UpdateSaleService):
        self.uow = uow
        self.service = service

    async def execute(
        self,
        id: UUID,
        data: SaleUpdateValueObject,
    ) -> SaleEntity:
        async with self.uow as uow:
            repository = uow.get_repository(ISalesRepository)
            result = await self.service.update_sale(
                id=id,
                data=data,
                repository=repository,
            )
            await uow.commit()
            return result
