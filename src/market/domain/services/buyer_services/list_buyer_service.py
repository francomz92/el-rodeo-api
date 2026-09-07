from typing import Literal
from uuid import UUID

from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.repositories.buyers import IBuyersRepository
from src.market.domain.value_objects.buyer_value_objects import BuyerListQueryParamsValueObject

BuyerOrderByField = Literal["name", "created_at"]


class ListBuyerService:
    async def get_buyers(
        self,
        filters: BuyerListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: BuyerOrderByField,
        repository: IBuyersRepository,
        user_id: UUID | None = None,
    ) -> list[BuyerEntity]:
        # user_id is passed through to the repository for future filtering
        return await repository.list_for_user(
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
            user_id=user_id,
        )
