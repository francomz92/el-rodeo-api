from src.common.application.ports.uow import IUoW
from src.market.domain.entities.sales import SaleEntity
from src.market.domain.repositories.sales import ISalesRepository
from src.market.domain.services.sale_services.create_sale_service import CreateSaleService
from src.market.domain.value_objects.sale_value_objects import SaleCreateValueObject


class CreateSaleCase:
    def __init__(self, uow: IUoW, service: CreateSaleService):
        self.uow = uow
        self.service = service

    async def execute(self, data: SaleCreateValueObject) -> SaleEntity:
        self.service.validate_data(data)
        async with self.uow as uow:
            repository = uow.get_repository(ISalesRepository)
            entity = await self.service.create_new(data, repository)
            await uow.commit()
            return entity
