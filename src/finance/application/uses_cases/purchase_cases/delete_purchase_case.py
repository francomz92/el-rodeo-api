from uuid import UUID

from src.auth.domain.entities._user_role import UserRole
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotPermissionError
from src.finance.domain.constants.purchases import PurchaseStatus
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
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

    async def execute(self, id: UUID, user_role_rank: int) -> None:
        async with self.uow as uow:
            repository = uow.get_repository(IPurchasesRepository)
            await self.service.validate_existence(
                id=id,
                repository=repository,
            )
            purchase = await repository.get_by_id(id=id)
            if purchase is not None:
                if purchase.status == PurchaseStatus.CONFIRMED:
                    # Deleting a confirmed purchase rolls back its stock entry
                    if user_role_rank < UserRole.ADMIN.rank:
                        raise NotPermissionError("Solo un admin o superior puede eliminar una compra confirmada")
                    supply_repository = uow.get_repository(IAnimalSuppliesRepository)
                    await supply_repository.decrease_stock(
                        id=purchase.supply_id,
                        amount_to_decrease=purchase.amount,
                    )
            await self.service.delete_purchase(
                id=id,
                repository=repository,
            )
            await uow.commit()
