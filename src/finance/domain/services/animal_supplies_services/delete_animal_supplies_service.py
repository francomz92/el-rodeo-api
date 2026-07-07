from uuid import UUID

from src.common.domain.exceptions import ConflictError, NotFoundError
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository


class DeleteAnimalSuppliesService:
    async def validate_delete(
        self,
        id: UUID,
        repository: IAnimalSuppliesRepository,
    ) -> None:
        supply = await repository.get_by_id(id=id)
        if not supply:
            raise NotFoundError("Insumo no encontrado")
        if supply.amount > 0:
            raise ConflictError("No puede eliminar un insumo con existencias.")

    async def delete_supply(
        self,
        id: UUID,
        repository: IAnimalSuppliesRepository,
    ) -> None:
        await repository.delete(id=id)
