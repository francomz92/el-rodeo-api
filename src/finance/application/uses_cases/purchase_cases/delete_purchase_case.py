from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.services.purchase_services.delete_purchase_service import DeletePurchaseService


class DeletePurchaseCase:
    def __init__(
        self,
        uow: IUoW,
        service: DeletePurchaseService,
    ):
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID, user_id: UUID) -> None:
        async with self.uow as uow:
            repository = uow.get_repository(IPurchasesRepository)
            await self.service.validate_purchase_exists(
                id=id,
                user_id=user_id,
                repository=repository,
            )
            await self.service.delete_purchase(
                id=id,
                user_id=user_id,
                repository=repository,
            )
            await uow.commit()
