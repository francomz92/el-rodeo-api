from uuid import UUID

from src.common.domain.exceptions import BusinessValidationError
from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.value_objects.animal_supplies_value_objects import AnimalSuppliesUpdateValueObject


class UpdateAnimalSuppliesService:
    def validate_data(self, data: AnimalSuppliesUpdateValueObject) -> None:
        if data.critical_amount >= data.amount:
            raise BusinessValidationError(
                message="Hay valores ingresados inconsistentes.",
                details=[
                    {
                        "field": "critical_amount",
                        "message": "La cantidad crítica debe ser menor que la cantidad disponible.",
                    }
                ],
            )

    async def update_animal_supplies(
        self,
        id: UUID,
        user_id: UUID,
        data: AnimalSuppliesUpdateValueObject,
        repository: IAnimalSuppliesRepository,
    ) -> AnimalSupplyEntity:
        return await repository.update_data(id, user_id, data)
