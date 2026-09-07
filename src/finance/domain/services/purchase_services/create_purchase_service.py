from uuid import UUID

from src.common.domain.exceptions import BusinessValidationError
from src.common.utils.date_utils import get_current_datetime
from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.value_objects.purchase_value_objects import PurchaseCreateValueObject


class CreatePurchaseService:
    def validate_data(self, data: PurchaseCreateValueObject):
        common_message = "Hay datos ingresados que no son válidos"
        if data.amount <= 0:
            raise BusinessValidationError(
                message=common_message,
                details=[
                    {
                        "field": "amount",
                        "message": "La cantidad debe ser mayor a 0",
                    }
                ],
            )
        if data.price <= 0:
            raise BusinessValidationError(
                message=common_message,
                details=[
                    {
                        "field": "price",
                        "message": "El precio debe ser mayor a 0",
                    }
                ],
            )
        if data.unit_price <= 0:
            raise BusinessValidationError(
                message=common_message,
                details=[
                    {
                        "field": "unit_price",
                        "message": "El precio unitario debe ser mayor a 0",
                    }
                ],
            )
        if data.purchase_date > get_current_datetime().date():
            raise BusinessValidationError(
                message=common_message,
                details=[
                    {
                        "field": "purchase_date",
                        "message": "La fecha de compra no puede ser mayor a la fecha actual",
                    }
                ],
            )

    async def validate_supply(
        self,
        supply_id: UUID,
        supply_repository: IAnimalSuppliesRepository,
    ) -> None:
        supply = await supply_repository.get_by_id(id=supply_id)
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

    async def create_new_purchase(
        self,
        user_id: UUID,
        data: PurchaseCreateValueObject,
        repository: IPurchasesRepository,
        supply_repository: IAnimalSuppliesRepository,
    ) -> PurchaseEntity:
        self.validate_data(data)
        await self.validate_supply(data.supply_id, supply_repository)
        return await repository.create(user_id=user_id, data=data)
