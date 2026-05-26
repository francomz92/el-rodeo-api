from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.repositoriyes.buyers import IBuyersRepository
from src.market.domain.services.buyer_services.list_buyer_service import ListBuyerService
from src.market.domain.value_objects.buyer_value_objects import BuyerListQueryParamsValueObject


class ListBuyerCase:
    def __init__(self, uow: IUoW, service: ListBuyerService):
        self.uow = uow
        self.service = service

    async def execute(
        self,
        user_id: UUID,
        filters: BuyerListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[BuyerEntity]:
        async with self.uow as uow:
            repository = uow.get_repository(IBuyersRepository)
            return await self.service.get_buyers(
                user_id=user_id,
                filters=filters,
                limit=limit,
                offset=offset,
                order_by=order_by,
                repository=repository,
            )
