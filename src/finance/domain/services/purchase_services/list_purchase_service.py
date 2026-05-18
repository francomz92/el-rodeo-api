from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.purchases import IPurchasesRepository
from uuid import UUID

from src.finance.domain.value_objetcts.purchase_value_objects import PurchaseListQueryParamValueObject


class ListPurchaseService:
    async def list_purchases(
        self,
        user_id: UUID,
        filters: PurchaseListQueryParamValueObject,
        limit: int,
        offset: int,
        order_by: str,
        repository: IPurchasesRepository,
    ) -> list[PurchaseEntity]:
        return await repository.list_for_user(
            user_id=user_id,
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
