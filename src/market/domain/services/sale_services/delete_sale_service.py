from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.market.domain.repositoriyes.sales import ISalesRepository


class DeleteSaleService:
    async def validate_sale_exists(
        self,
        id: UUID,
        user_id: UUID,
        repository: ISalesRepository,
    ) -> None:
        sale_exists = await repository.exists(id, user_id)
        if not sale_exists:
            raise NotFoundError("La venta que intenta eliminar no existe.")

    async def delete_sale(
        self,
        id: UUID,
        repository: ISalesRepository,
    ) -> None:
        await repository.delete(id)
