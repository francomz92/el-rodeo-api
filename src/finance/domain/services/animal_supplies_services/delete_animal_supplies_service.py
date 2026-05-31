from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository


class DeleteAnimalSuppliesService:
    async def validate_exists(
        self,
        id: UUID,
        user_id: UUID,
        repository: IAnimalSuppliesRepository,
    ) -> None:
        if not await repository.exists(id, user_id):
            raise NotFoundError("El insumo que intenta eliminar no existe.")

    async def delete_animal_supplies(
        self,
        id: UUID,
        repository: IAnimalSuppliesRepository,
    ) -> None:
        await repository.delete(id)
