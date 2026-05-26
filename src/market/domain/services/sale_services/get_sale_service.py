from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.market.domain.entities.sales import SaleEntity
from src.market.domain.repositoriyes.sales import ISalesRepository


class GetSaleService:
    async def get_sale(
        self,
        id: UUID,
        user_id: UUID,
        repository: ISalesRepository,
    ) -> SaleEntity:
        sale = await repository.get_by_id(id, user_id)
        if sale is None:
            raise NotFoundError("No se encontró la venta.")
        return sale
