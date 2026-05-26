from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.purchases import IPurchasesRepository


class GetPurchaseService:
    async def get_purchase(
        self,
        id: UUID,
        user_id: UUID,
        repository: IPurchasesRepository,
    ) -> PurchaseEntity:
        purchase = await repository.get_by_id(id, user_id)
        if purchase is None:
            raise NotFoundError("La compra no fue encontrada")
        return purchase
