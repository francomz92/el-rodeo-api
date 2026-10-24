from uuid import UUID

from src.common.domain.exceptions import BusinessValidationError, NotFoundError
from src.finance.domain.constants.purchases import PurchaseStatus
from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.services.purchase_services.create_purchase_service import assert_purchase_unit_matches

ALREADY_CONFIRMED_MESSAGE = "Esta compra ya fue confirmada"


class ConfirmPurchaseService:
    async def confirm_purchase(
        self,
        purchase: PurchaseEntity,
        user_id: UUID,
        repository: IPurchasesRepository,
        supply_repository: IAnimalSuppliesRepository,
    ) -> PurchaseEntity:
        if purchase.status != PurchaseStatus.PENDING:
            raise BusinessValidationError(message=ALREADY_CONFIRMED_MESSAGE)
        supply = await supply_repository.get_by_id(id=purchase.supply_id)
        if not supply:
            raise BusinessValidationError(
                message="Verifique el suministro seleccionado",
                details=[
                    {
                        "field": "supply_id",
                        "message": "El suministro seleccionado no existe.",
                    },
                ],
            )
        assert_purchase_unit_matches(purchase.unit_of_measurement, supply)
        confirmed = await repository.mark_confirmed(id=purchase.id, confirmed_by=user_id)
        if not confirmed:
            # Concurrent confirmation won the race between the check and the update
            raise BusinessValidationError(message=ALREADY_CONFIRMED_MESSAGE)
        updated = await repository.get_by_id(id=purchase.id)
        if updated is None:
            raise NotFoundError("Compra no encontrada")
        return updated
