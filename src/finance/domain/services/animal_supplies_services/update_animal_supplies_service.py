from uuid import UUID

from src.common.domain.exceptions import ConflictError, NotFoundError
from src.common.domain.types import Sentinel
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.value_objects.animal_supplies_value_objects import AnimalSuppliesUpdateValueObject


class UpdateAnimalSuppliesService:
    async def validate_update(
        self,
        id: UUID,
        data: AnimalSuppliesUpdateValueObject,
        repository: IAnimalSuppliesRepository,
    ) -> None:
        supply = await repository.get_by_id(id=id)
        if not supply:
            raise NotFoundError("El insumo a actualizar no existe.")
        if data.critical_amount is not Sentinel.UNSET and data.amount is not Sentinel.UNSET and data.critical_amount >= data.amount:
            raise ConflictError("La cantidad crítica debe ser superior a la cantidad de existencias")

    async def update_supply(
        self,
        id: UUID,
        data: AnimalSuppliesUpdateValueObject,
        repository: IAnimalSuppliesRepository,
    ) -> None:
        return await repository.update_data(id=id, data=data)
