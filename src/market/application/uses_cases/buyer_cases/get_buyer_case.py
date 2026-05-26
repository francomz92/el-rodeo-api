from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.repositoriyes.buyers import IBuyersRepository
from src.market.domain.services.buyer_services.get_buyer_service import GetBuyerService


class GetBuyerCase:
    def __init__(self, uow: IUoW, service: GetBuyerService):
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID, user_id: UUID) -> BuyerEntity:
        async with self.uow as uow:
            repository = uow.get_repository(IBuyersRepository)
            return await self.service.get_buyer(
                id=id,
                user_id=user_id,
                repository=repository,
            )
