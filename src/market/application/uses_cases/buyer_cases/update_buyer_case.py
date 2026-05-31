from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.repositories.buyers import IBuyersRepository
from src.market.domain.services.buyer_services.update_buyer_service import UpdateBuyerService
from src.market.domain.value_objects.buyer_value_objects import BuyerUpdateValueObject


class UpdateBuyerCase:
    def __init__(self, uow: IUoW, service: UpdateBuyerService):
        self.uow = uow
        self.service = service

    async def execute(
        self,
        id: UUID,
        user_id: UUID,
        data: BuyerUpdateValueObject,
    ) -> BuyerEntity:
        async with self.uow as uow:
            repository = uow.get_repository(IBuyersRepository)
            await self.service.validate_buyer_exists(
                id=id,
                user_id=user_id,
                repository=repository,
            )
            result = await self.service.update_buyer(
                repository=repository,
                id=id,
                user_id=user_id,
                data=data,
            )
            await uow.commit()
            return result
