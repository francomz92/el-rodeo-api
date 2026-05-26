from uuid import UUID

from src.common.domain.exceptions import BusinessValidationError
from src.common.utils.date_utils import get_current_datetime
from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.value_objetcts.purchase_value_objects import PurchaseCreateValueObject


class CreatePurchaseService:
    def validate_data(self, data: PurchaseCreateValueObject):
        comon_message = "Hay datos ingresados que no son válidos"
        if data.amount <= 0:
            raise BusinessValidationError(
                message=comon_message,
                details=[
                    {
                        "field": "amount",
                        "message": "La cantidad debe ser mayor a 0",
                    }
                ],
            )
        if data.price <= 0:
            raise BusinessValidationError(
                message=comon_message,
                details=[
                    {
                        "field": "price",
                        "message": "El precio debe ser mayor a 0",
                    }
                ],
            )
        if data.unit_price <= 0:
            raise BusinessValidationError(
                message=comon_message,
                details=[
                    {
                        "field": "unit_price",
                        "message": "El precio unitario debe ser mayor a 0",
                    }
                ],
            )
        if data.purchase_date > get_current_datetime().date():
            raise BusinessValidationError(
                message=comon_message,
                details=[
                    {
                        "field": "purchase_date",
                        "message": "La fecha de compra no puede ser mayor a la fecha actual",
                    }
                ],
            )

    async def validate_supply_exists(
        self,
        supply_id: UUID,
        user_id: UUID,
        supply_repository: IAnimalSuppliesRepository,
    ) -> None:
        supply_exists = await supply_repository.exists(supply_id, user_id)
        if not supply_exists:
            raise BusinessValidationError(
                message="Verifique el suministro seleccionado",
                details=[
                    {
                        "field": "supply_id",
                        "message": "El suministro seleccionado no existe.",
                    },
                ],
            )

    async def create_new(
        self,
        user_id: UUID,
        data: PurchaseCreateValueObject,
        repository: IPurchasesRepository,
    ) -> PurchaseEntity:
        return await repository.create(user_id, data)

    async def incrase_supply_stock(
        self,
        supply_id: UUID,
        amount_to_incrase: float,
        supply_repository: IAnimalSuppliesRepository,
    ):

        await supply_repository.incrase_stock(supply_id, amount_to_incrase)
