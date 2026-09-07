from src.common.domain.exceptions import BusinessValidationError
from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.value_objects.animal_supplies_value_objects import (
    AnimalSuppliesCreateValueObject,
    AnimalSuppliesListQueryParamsValueObject,
)


class CreateAnimalSuppliesService:
    def validate_data(self, data: AnimalSuppliesCreateValueObject) -> None:
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

    async def validate_exists(self, data: AnimalSuppliesCreateValueObject, repository: IAnimalSuppliesRepository) -> None:
        filters = AnimalSuppliesListQueryParamsValueObject(
            name=data.name,
            type_id=data.type_id,
        )
        if await repository.list_for_user(filters=filters, limit=1, offset=0, order_by="id"):
            raise BusinessValidationError(message="Este suministro ya se encuentra cargado.")

    async def create_new(
        self,
        data: AnimalSuppliesCreateValueObject,
        repository: IAnimalSuppliesRepository,
    ) -> AnimalSupplyEntity:
        self.validate_data(data)
        return await repository.create(data)
