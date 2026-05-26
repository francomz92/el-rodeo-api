from uuid import UUID

from src.common.domain.exceptions import BusinessValidationError
from src.finance.domain.repositories.animal_supplie_types import ISupplyTypesRepository


class GetSupplyTypeService:
    async def validate_exists(
        self,
        id: UUID,
        repository: ISupplyTypesRepository,
    ) -> None:
        if not await repository.exists(id):
            raise BusinessValidationError(
                message="El tipo de suministro es requerido.",
                details=[
                    {
                        "field": "type_id",
                        "message": "El tipo de suministro seleccionado no exists.",
                    }
                ],
            )
