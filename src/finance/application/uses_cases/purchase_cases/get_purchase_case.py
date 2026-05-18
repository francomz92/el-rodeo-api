from src.finance.domain.entities.purchases import PurchaseEntity
from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.services.purchase_services.get_purchase_service import GetPurchaseService


class GetPurchaseCase:
    def __init__(
        self,
        uow: IUoW,
        service: GetPurchaseService,
    ):
        self.uow = uow
        self.service = service

    async def execute(
        self,
        id: UUID,
        user_id: UUID,
    ) -> PurchaseEntity:
        async with self.uow as uow:
            repository = uow.get_repository(IPurchasesRepository)
            return await self.service.get_purchase(
                id=id,
                user_id=user_id,
                repository=repository,
            )
