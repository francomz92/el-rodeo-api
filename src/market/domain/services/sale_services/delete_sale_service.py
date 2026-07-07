from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.market.domain.repositories.sales import ISalesRepository


class DeleteSaleService:
    async def validate_sale_exists(
        self,
        id: UUID,
        repository: ISalesRepository,
    ) -> None:
        sale = await repository.get_by_id(id)
        if not sale:
            raise NotFoundError("La venta que intenta eliminar no existe.")

    async def delete_sale(
        self,
        id: UUID,
        repository: ISalesRepository,
    ) -> None:
        await repository.delete(id)
