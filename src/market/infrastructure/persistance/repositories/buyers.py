from uuid import UUID

from sqlalchemy import delete, exists, insert, select, update

from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories.mixins import SessionMixin
from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.repositoriyes.buyers import IBuyersRepository
from src.market.domain.value_objects.buyer_value_objects import (
    BuyerCreateValueObject,
    BuyerListQueryParamsValueObject,
    BuyerUpdateValueObject,
)
from src.market.infrastructure.persistance.models import Buyer


class BuyersRepository(IBuyersRepository, SessionMixin):
    async def exists(self, id: UUID, user_id: UUID) -> bool:
        query = (
            exists(Buyer)
            .where(
                Buyer.id == id,
                Buyer.user_id == user_id,
            )
            .select()
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(
        self,
        id: UUID,
        user_id: UUID,
    ) -> BuyerEntity | None:
        query = select(Buyer).where(
            Buyer.id == id,
            Buyer.user_id == user_id,
        )
        result = await self.db.execute(query)
        buyer_db = result.scalar_one_or_none()
        return self._build_buyer(buyer_db) if buyer_db else None

    async def list_for_user(
        self,
        user_id: UUID,
        filters: BuyerListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[BuyerEntity]:
        kws = {k: v for k, v in vars(filters).items() if v is not Sentinel.UNSET}
        query = (
            select(Buyer)
            .where(
                Buyer.user_id == user_id,
            )
            .filter_by(**kws)
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
        )
        result = await self.db.execute(query)
        buyers_list = result.scalars().unique().all()
        return [self._build_buyer(buyer_data) for buyer_data in buyers_list]

    async def create(self, data: BuyerCreateValueObject) -> BuyerEntity:
        query = (
            insert(Buyer)
            .values(
                user_id=data.user_id,
                name=data.name,
                description=data.description,
                contact_number=data.contact_number,
                contact_address=data.contact_address,
            )
            .returning(Buyer.id)
        )
        result = await self.db.execute(query)
        buyer_id = result.scalar_one()
        return await self.get_by_id(buyer_id, data.user_id)  # type: ignore

    async def update_data(
        self,
        id: UUID,
        user_id: UUID,
        data: BuyerUpdateValueObject,
    ) -> BuyerEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        query = (
            update(Buyer)
            .where(
                Buyer.id == id,
                Buyer.user_id == user_id,
            )
            .values(**kws)
            .returning(Buyer.id)
        )
        result = await self.db.execute(query)
        buyer_id = result.scalar_one()
        return await self.get_by_id(buyer_id, user_id)  # type: ignore

    async def delete(self, id: UUID) -> None:
        query = delete(Buyer).where(Buyer.id == id)
        await self.db.execute(query)

    def _build_buyer(self, buyer_data: Buyer) -> BuyerEntity:
        return BuyerEntity(
            id=buyer_data.id,
            created_at=buyer_data.created_at,
            name=buyer_data.name,
            description=buyer_data.description,
            contact_number=buyer_data.contact_number,
            contact_address=buyer_data.contact_address,
        )
