from uuid import UUID

from src.common.domain.exceptions import BusinessValidationError, NotFoundError
from src.common.domain.types import Sentinel
from src.market.domain.entities.sales import SaleEntity
from src.market.domain.repositories.sales import ISalesRepository
from src.market.domain.value_objects.sale_value_objects import SaleUpdateValueObject


class UpdateSaleService:
    async def update_sale(
        self,
        id: UUID,
        data: SaleUpdateValueObject,
        repository: ISalesRepository,
    ) -> SaleEntity:
        if all(v is Sentinel.UNSET for v in vars(data).values()):
            raise BusinessValidationError(
                message="No hay campos para actualizar.",
                details=[{"field": "data", "message": "Debe especificar al menos un campo para actualizar."}],
            )
        result = await repository.update_data(id, data)
        if result is None:
            raise NotFoundError("La venta que intenta actualizar no existe.")
        return result
