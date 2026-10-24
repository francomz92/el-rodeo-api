from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotFoundError
from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.services.purchase_services.confirm_purchase_service import ConfirmPurchaseService


class ConfirmPurchaseCase:
    def __init__(self, uow: IUoW, service: ConfirmPurchaseService):
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID, user_id: UUID) -> PurchaseEntity:
        async with self.uow as uow:
            repository = uow.get_repository(IPurchasesRepository)
            purchase = await repository.get_by_id(id=id)
            if not purchase:
                raise NotFoundError("Compra no encontrada")
            supply_repository = uow.get_repository(IAnimalSuppliesRepository)
            purchase = await self.service.confirm_purchase(
                purchase=purchase,
                user_id=user_id,
                repository=repository,
                supply_repository=supply_repository,
            )
            # Stock is added here, once, atomically with the status transition
            await supply_repository.increase_stock(
                id=purchase.supply_id,
                amount_to_increase=purchase.amount,
            )
            await uow.commit()
            return purchase
