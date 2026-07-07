from src.finance.domain.repositories.purchases import IPurchasesRepository


class ListPurchaseService:
    async def get_purchases(
        self,
        repository: IPurchasesRepository,
        query,
        limit: int,
        offset: int,
        order_by: str,
    ):
        purchases = await repository.list_for_user(
            filters=query,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
        return purchases
