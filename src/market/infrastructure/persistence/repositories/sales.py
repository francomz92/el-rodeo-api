from datetime import date
from uuid import UUID

from sqlalchemy import RowMapping, delete, exists, func, insert, select, update

from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.entities.animal_entity import AnimalEntity, AnimalTypeEntity
from src.cattle.infrastructure.persistence.models import AnimalType
from src.cattle.infrastructure.persistence.models._animal_models import Animal
from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)
from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.entities.sales import SaleEntity
from src.market.domain.repositories.sales import ISalesRepository
from src.market.domain.value_objects.sale_value_objects import SaleCreateValueObject, SaleListQueryParamsValueObject
from src.market.infrastructure.persistence.models import Buyer, Sale


class SalesRepository(ISalesRepository, TenantAwareRepository, AuditableRepositoryMixin):
    _model: type[Sale] = Sale

    async def exists(self, id: UUID) -> bool:
        query = self._filter_tenant(exists(Sale).where(Sale.id == id).select())
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(
        self,
        id: UUID,
    ) -> SaleEntity | None:
        query = self._filter_tenant(
            select(
                *Sale.__table__.columns,
                Buyer.created_at.label("buyer_created_at"),
                Buyer.name.label("buyer_name"),
                Buyer.description.label("buyer_description"),
                Buyer.contact_number.label("buyer_contact_number"),
                Buyer.contact_address.label("buyer_contact_address"),
                Animal.caravana.label("animal_caravana"),
                Animal.tag.label("animal_tag"),
                Animal.date_of_birth.label("animal_date_of_birth"),
                Animal.initial_weight.label("animal_initial_weight"),
                Animal.initial_weight_date.label("animal_initial_weight_date"),
                Animal.last_weight.label("animal_last_weight"),
                Animal.breed.label("animal_breed"),
                Animal.status.label("animal_status"),
                AnimalType.id.label("animal_type_id"),
                AnimalType.name.label("animal_type_name"),
            )
            .where(Sale.id == id)
            .outerjoin(Buyer, Sale.buyer_id == Buyer.id)
            .outerjoin(Animal, Sale.animal_id == Animal.id)
            .outerjoin(AnimalType, Animal.type_id == AnimalType.id)
        )
        result = await self.db.execute(query)
        sale_db = result.mappings().one_or_none()
        return self._build_sale(sale_db) if sale_db else None

    async def list_for_user(
        self,
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
            else:
                conditions.append(getattr(Sale, k) == v)
        query = self._filter_tenant(
            select(
                *Sale.__table__.columns,
                Buyer.created_at.label("buyer_created_at"),
                Buyer.name.label("buyer_name"),
                Buyer.description.label("buyer_description"),
                Buyer.contact_number.label("buyer_contact_number"),
                Buyer.contact_address.label("buyer_contact_address"),
                Animal.caravana.label("animal_caravana"),
                Animal.tag.label("animal_tag"),
                Animal.date_of_birth.label("animal_date_of_birth"),
                Animal.initial_weight.label("animal_initial_weight"),
                Animal.initial_weight_date.label("animal_initial_weight_date"),
                Animal.last_weight.label("animal_last_weight"),
                Animal.breed.label("animal_breed"),
                Animal.status.label("animal_status"),
                AnimalType.id.label("animal_type_id"),
                AnimalType.name.label("animal_type_name"),
            )
            .where(*conditions)
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
            .outerjoin(Buyer, Sale.buyer_id == Buyer.id)
            .outerjoin(Animal, Sale.animal_id == Animal.id)
            .outerjoin(AnimalType, Animal.type_id == AnimalType.id)
        )
        result = await self.db.execute(query)
        sales_list_db = result.mappings().all()
        return [self._build_sale(sale_data) for sale_data in sales_list_db]

    async def create(self, data: SaleCreateValueObject) -> SaleEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        kws["tenant_id"] = self._tenant_id
        query = insert(Sale).values(**kws).returning(Sale.id)
        result = await self.db.execute(query)
        sale_id = result.scalar_one()
        new_entity = await self.get_by_id(sale_id)
        self._audit_create("sale", sale_id, kws)
        return new_entity  # type: ignore[return-value]

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
        # Capture old values before update
        old_row = await self.db.execute(self._filter_tenant(select(Sale.__table__).where(Sale.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        new_values = {
            "buyer_id": str(buyer_id),
            "animal_id": str(animal_id),
            "sale_date": str(sale_date) if isinstance(sale_date, date) else sale_date,
            "price": price,
            "price_per_kg": price_per_kg,
            "weight": weight,
            "description": description,
        }
        query = self._filter_tenant(
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
                updated_at=func.now(),
            )
        )
        await self.db.execute(query)
        self._audit_update("sale", id, old_values, new_values)

    async def delete(self, id: UUID) -> None:
        # Capture old values before delete
        old_row = await self.db.execute(self._filter_tenant(select(Sale.__table__).where(Sale.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        query = self._filter_tenant(delete(Sale).where(Sale.id == id))
        await self.db.execute(query)
        self._audit_delete("sale", id, old_values)

    def _build_sale(self, sale_data: RowMapping) -> SaleEntity:
        buyer_entity = (
            BuyerEntity(
                id=sale_data["buyer_id"],
                tenant_id=sale_data["tenant_id"],
                created_at=sale_data["buyer_created_at"],
                name=sale_data["buyer_name"],
                description=sale_data["buyer_description"],
                contact_number=sale_data["buyer_contact_number"],
                contact_address=sale_data["buyer_contact_address"],
            )
            if sale_data["buyer_id"]
            else None
        )

        animal_type_entity = (
            AnimalTypeEntity(
                id=sale_data["animal_type_id"],
                name=sale_data["animal_type_name"],
            )
            if sale_data["animal_type_id"]
            else None
        )

        animal_entity = (
            AnimalEntity(
                id=sale_data["animal_id"],
                tenant_id=sale_data["tenant_id"],
                caravana=sale_data["animal_caravana"],
                tag=sale_data["animal_tag"],
                date_of_birth=sale_data["animal_date_of_birth"],
                initial_weight=sale_data["animal_initial_weight"],
                initial_weight_date=sale_data["animal_initial_weight_date"],
                last_weight=sale_data["animal_last_weight"],
                breed=sale_data["animal_breed"],
                status=AnimalStatus(sale_data["animal_status"]),
                type=animal_type_entity,
            )
            if sale_data["animal_id"]
            else None
        )

        return SaleEntity(
            id=sale_data["id"],
            tenant_id=sale_data["tenant_id"],
            sale_date=sale_data["sale_date"],
            price=sale_data["price"],
            price_per_kg=sale_data["price_per_kg"],
            weight=sale_data["weight"],
            description=sale_data["description"],
            buyer=buyer_entity,
            animal=animal_entity,
        )
