from datetime import date
from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import joinedload

from src.common.infrastructure.persistence.connections.db import AsyncSession
from src.market.application.ports.repositoriyes.sales import ISalesRepository
from src.market.domain.entities.sales import SaleEntity
from src.market.infrastructure.persistance.models import Sale


class SalesRepository(ISalesRepository):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, id: UUID, user_id: UUID) -> SaleEntity | None:
        query = (
            select(Sale)
            .where(Sale.id == id, Sale.user_id == user_id)
            .options(
                joinedload(Sale.buyer, Sale.animal),
            )
        )
        result = await self.db.execute(query)
        sale_db = result.scalar_one_or_none()
        return self._build_sale(sale_db) if sale_db else None

    async def list_all(self, user_id: UUID) -> list[SaleEntity]:
        query = (
            select(Sale)
            .where(Sale.user_id == user_id)
            .options(
                joinedload(Sale.buyer, Sale.animal),
            )
        )
        result = await self.db.execute(query)
        sales_list_db = result.scalars().unique().all()
        return [self._build_sale(sale_data) for sale_data in sales_list_db]

    async def create(
        self,
        user_id: UUID,
        buyer_id: UUID,
        animal_id: UUID,
        sale_date: date,
        price: float,
        price_per_kg: float,
        weight: float,
        description: str,
    ) -> None:
        query = insert(Sale).values(
            user_id=user_id,
            buyer_id=buyer_id,
            animal_id=animal_id,
            sale_date=sale_date,
            price=price,
            price_per_kg=price_per_kg,
            weight=weight,
            description=description,
        )
        await self.db.execute(query)

    async def update_data(
        self,
        id: UUID,
        buyer_id: UUID,
        animal_id: UUID,
        sale_date: date,
        price: float,
        price_per_kg: float,
        weight: float,
        description: str,
    ) -> None:
        query = (
            update(Sale)
            .where(Sale.id == id)
            .values(
                buyer_id=buyer_id,
                animal_id=animal_id,
                sale_date=sale_date,
                price=price,
                price_per_kg=price_per_kg,
                weight=weight,
                description=description,
            )
        )
        await self.db.execute(query)

    async def delete(self, id: UUID) -> None:
        query = delete(Sale).where(Sale.id == id)
        await self.db.execute(query)

    def _build_sale(self, sale_data: Sale) -> SaleEntity:
        return SaleEntity(
            id=sale_data.id,
            sale_date=sale_data.sale_date,
            price=sale_data.price,
            price_per_kg=sale_data.price_per_kg,
            weight=sale_data.weight,
            description=sale_data.description,
            buyer=sale_data.buyer,
            animal=sale_data.animal,
        )
