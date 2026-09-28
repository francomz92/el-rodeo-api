from typing import cast
from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.repositories.user_reader_port import IUserNameReader
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
    ) -> PurchaseEntity:
        async with self.uow as uow:
            repository = uow.get_repository(IPurchasesRepository)
            purchase = await self.service.validate_existence(
                id=id,
                repository=repository,
            )
            user_reader = uow.get_repository(IUserNameReader)
            user_names = await user_reader.get_names_by_ids({purchase.user_id})
            purchase.user_name = cast(str, user_names.get(purchase.user_id))
            return purchase
