from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.market.domain.repositoriyes.buyers import IBuyersRepository
from src.market.domain.services.buyer_services.delete_buyer_service import DeleteBuyerService


class DeleteBuyerCase:
    def __init__(self, uow: IUoW, service: DeleteBuyerService):
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID, user_id: UUID) -> None:
        async with self.uow as uow:
            repository = uow.get_repository(IBuyersRepository)
            await self.service.validate_buyer_exists(
                id=id,
                user_id=user_id,
                repository=repository,
            )
            await self.service.delete_buyer(id, repository)
