from datetime import date
from uuid import UUID

from sqlalchemy import delete, exists, insert, select, update
from sqlalchemy.orm import joinedload

from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.entities.animal_entity import AnimalEntity, AnimalTypeEntity
from src.cattle.infrastructure.persistence.models._animal_models import Animal
from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories.mixins import SessionMixin
from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.entities.sales import SaleEntity
from src.market.domain.repositories.sales import ISalesRepository
from src.market.domain.value_objects.sale_value_objects import SaleCreateValueObject, SaleListQueryParamsValueObject
from src.market.infrastructure.persistence.models import Sale


class SalesRepository(ISalesRepository, SessionMixin):
    async def exists(self, id: UUID, user_id: UUID) -> bool:
        query = (
            exists(Sale)
            .where(
                Sale.id == id,
                Sale.user_id == user_id,
            )
            .select()
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(
        self,
        id: UUID,
        user_id: UUID,
    ) -> SaleEntity | None:
        query = (
            select(Sale)
            .where(Sale.id == id, Sale.user_id == user_id)
            .options(
                joinedload(Sale.buyer),
                joinedload(Sale.animal).joinedload(Animal.type),
            )
        )
        result = await self.db.execute(query)
        sale_db = result.scalar_one_or_none()
        return self._build_sale(sale_db) if sale_db else None

    async def list_for_user(
        self,
        user_id: UUID,
        filters: SaleListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[SaleEntity]:
        conditions = []
        for k, v in vars(filters).items():
            if v is Sentinel.UNSET:
                continue
            elif k == "price":
                conditions.append(Sale.price <= v)
            elif k in ("buyer_id", "sale_date"):
                conditions.append(getattr(Sale, k) == v)
        query = (
            select(Sale)
            .where(
                Sale.user_id == user_id,
                *conditions,
            )
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
            .options(
                joinedload(Sale.buyer),
                joinedload(Sale.animal).joinedload(Animal.type),
            )
        )
        result = await self.db.execute(query)
        sales_list_db = result.scalars().unique().all()
        return [self._build_sale(sale_data) for sale_data in sales_list_db]

    async def create(self, data: SaleCreateValueObject) -> SaleEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        query = insert(Sale).values(**kws).returning(Sale.id)
        result = await self.db.execute(query)
        sale_id = result.scalar_one()
        return await self.get_by_id(sale_id, data.user_id)  # type: ignore

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
        buyer_entity: BuyerEntity | None = None
        if sale_data.buyer is not None:
            b = sale_data.buyer
            buyer_entity = BuyerEntity(
                id=b.id,
                created_at=b.created_at,
                name=b.name,
                description=b.description,
                contact_number=b.contact_number,
                contact_address=b.contact_address,
            )

        animal_entity: AnimalEntity | None = None
        if sale_data.animal is not None:
            a = sale_data.animal
            animal_type_entity: AnimalTypeEntity | None = None
            if a.type is not None:
                animal_type_entity = AnimalTypeEntity(
                    id=a.type.id,
                    name=a.type.name,
                )
            animal_entity = AnimalEntity(
                id=a.id,
                caravana=a.caravana,
                name=a.name,
                tag=a.tag,
                date_of_birth=a.date_of_birth,
                initial_weight=a.initial_weight,
                initial_weight_date=a.initial_weight_date,
                last_weight=a.last_weight,
                breed=a.breed,
                status=AnimalStatus(a.status),
                type=animal_type_entity,
            )

        return SaleEntity(
            id=sale_data.id,
            sale_date=sale_data.sale_date,
            price=sale_data.price,
            price_per_kg=sale_data.price_per_kg,
            weight=sale_data.weight,
            description=sale_data.description,
            buyer=buyer_entity,
            animal=animal_entity,
        )
