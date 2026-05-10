from uuid import UUID

from sqlalchemy import delete, insert, select, update

from src.common.infrastructure.persistence.repositories.mixins import SessionMixin
from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.repositoriyes.buyers import IBuyersRepository
from src.market.infrastructure.persistance.models import Buyer


class BuyersRepository(IBuyersRepository, SessionMixin):
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

    async def list_all(self, user_id: UUID) -> list[BuyerEntity]:
        query = select(Buyer).where(Buyer.user_id == user_id)
        result = await self.db.execute(query)
        buyers_list = result.scalars().unique().all()
        return [self._build_buyer(buyer_data) for buyer_data in buyers_list]

    async def create(
        self,
        user_id: UUID,
        name: str,
        description: str,
        contact_number: str,
        contact_address: str,
    ) -> None:
        query = insert(Buyer).values(
            user_id=user_id,
            name=name,
            description=description,
            contact_number=contact_number,
            contact_address=contact_address,
        )
        await self.db.execute(query)

    async def update_data(
        self,
        id: UUID,
        user_id: UUID,
        name: str,
        description: str,
        contact_number: str,
        contact_address: str,
    ) -> None:
        query = (
            update(Buyer)
            .where(
                Buyer.id == id,
                Buyer.user_id == user_id,
            )
            .values(
                name=name,
                description=description,
                contact_number=contact_number,
                contact_address=contact_address,
            )
        )
        await self.db.execute(query)

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
