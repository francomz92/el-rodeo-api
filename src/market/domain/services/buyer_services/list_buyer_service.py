from uuid import UUID

from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.repositories.buyers import IBuyersRepository
from src.market.domain.value_objects.buyer_value_objects import BuyerListQueryParamsValueObject


class ListBuyerService:
    async def get_buyers(
        self,
        user_id: UUID,
        filters: BuyerListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
        repository: IBuyersRepository,
    ) -> list[BuyerEntity]:
        return await repository.list_for_user(
            user_id=user_id,
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
