from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.purchases import IPurchasesRepository


class GetPurchaseService:
    async def validate_existence(
        self,
        id: UUID,
        repository: IPurchasesRepository,
    ) -> PurchaseEntity:
        purchase = await repository.get_by_id(id=id)
        if not purchase:
            raise NotFoundError("Compra no encontrada")
        return purchase
