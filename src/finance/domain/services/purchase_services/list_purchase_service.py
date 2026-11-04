from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.value_objects.purchase_value_objects import PurchaseListQueryParamValueObject


class ListPurchaseService:
    async def get_purchases(
        self,
        repository: IPurchasesRepository,
        query: PurchaseListQueryParamValueObject,
        limit: int,
        offset: int,
        order_by: str,
        cursor: str | None = None,
    ) -> tuple[list[PurchaseEntity], int, bool]:
        """List purchases matching *query* filters.

        Returns ``(items, total_count, has_next)``. When *cursor* is
        provided the repository walks the keyset page after that token.
        """
        return await repository.list_for_user(
            filters=query,
            limit=limit,
            offset=offset,
            order_by=order_by,
            cursor=cursor,
        )
