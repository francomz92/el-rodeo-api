from src.common.application.ports.uow import IUoW
from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.repositories.buyers import IBuyersRepository
from src.market.domain.services.buyer_services.create_buyer_service import CreateBuyerService
from src.market.domain.value_objects.buyer_value_objects import BuyerCreateValueObject


class CreateBuyerCase:
    def __init__(self, uow: IUoW, service: CreateBuyerService):
        self.uow = uow
        self.service = service

    async def execute(self, data: BuyerCreateValueObject) -> BuyerEntity:
        async with self.uow as uow:
            repository = uow.get_repository(IBuyersRepository)
            result = await self.service.create_new(data, repository)
            await uow.commit()
            return result
