from uuid import UUID

from src.common.domain.exceptions import ConflictError, NotFoundError
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository


class UpdateAnimalSuppliesService:
    async def validate_update(
        self,
        id: UUID,
        repository: IAnimalSuppliesRepository,
    ) -> None:
        supply = await repository.get_by_id(id=id)
        if not supply:
            raise NotFoundError("El insumo a actualizar no existe.")
        if supply.amount > supply.critical_amount:
            raise ConflictError("La cantidad crítica debe ser superior a la cantidad de existencias")

    async def update_supply(
        self,
        id: UUID,
        data,
        repository: IAnimalSuppliesRepository,
    ):
        return await repository.update_data(id=id, data=data)
