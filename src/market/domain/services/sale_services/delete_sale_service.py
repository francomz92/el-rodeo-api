from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.market.domain.repositories.sales import ISalesRepository


class DeleteSaleService:
    async def delete_sale(
        self,
        id: UUID,
        repository: ISalesRepository,
    ) -> None:
        deleted = await repository.delete(id)
        if not deleted:
            raise NotFoundError("La venta que intenta eliminar no existe.")
