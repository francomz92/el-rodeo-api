from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.finance.domain.repositories.animal_supplie_types import ISupplyTypesRepository


class DeleteAnimalSupplyTypeService:
    async def validate_exists(
        self,
        id: UUID,
        repository: ISupplyTypesRepository,
    ) -> None:
        exists = await repository.exists(id)
        if not exists:
            raise NotFoundError("El tipo de suministro que intenta eliminar no existe.")

    async def delete(
        self,
        id: UUID,
        repository: ISupplyTypesRepository,
    ) -> None:
        await repository.delete(id)
