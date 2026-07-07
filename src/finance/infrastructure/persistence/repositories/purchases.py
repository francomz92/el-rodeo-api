from datetime import date
from uuid import UUID

from sqlalchemy import RowMapping, delete, exists, func, insert, select, update

from src.auth.infrastructure.persistence.models import User
from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)
from src.finance.domain.constants.animal_supplies import UnitOfMeasurement
from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.value_objects.purchase_value_objects import PurchaseCreateValueObject, PurchaseListQueryParamValueObject
from src.finance.infrastructure.persistence.models import AnimalSupply, Purchase


class PurchasesRepository(IPurchasesRepository, TenantAwareRepository, AuditableRepositoryMixin):
    _model: type[Purchase] = Purchase

    async def exists(self, id: UUID) -> bool:
        query = self._filter_tenant(exists(Purchase).where(Purchase.id == id).select())
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(
        self,
        id: UUID,
    ) -> PurchaseEntity | None:
        query = self._filter_tenant(
            select(
                *Purchase.__table__.columns,
                User.name.label("user_name"),
                AnimalSupply.name.label("supply_name"),
            )
            .where(Purchase.id == id)
            .outerjoin(AnimalSupply, Purchase.supply_id == AnimalSupply.id)
            .outerjoin(User, Purchase.user_id == User.id)
        )
        result = await self.db.execute(query)
        purchase_db = result.mappings().one_or_none()
        return self._build_purchase_with_user_and_supply(purchase_db) if purchase_db else None

    async def list_for_user(
        self,
        filters: PurchaseListQueryParamValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[PurchaseEntity]:
        conditions = []
        for k, v in vars(filters).items():
            if v is Sentinel.UNSET:
                continue
            elif k in (
                "id",
                "supply_id",
                "purchase_date",
                "unit_of_measurement",
            ):
                conditions.append(getattr(Purchase, k) == v)
        query = self._filter_tenant(
            select(
                *Purchase.__table__.columns,
                User.name.label("user_name"),
                AnimalSupply.name.label("supply_name"),
            )
            .where(*conditions)
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
            .outerjoin(User, Purchase.user_id == User.id)
            .outerjoin(AnimalSupply, Purchase.supply_id == AnimalSupply.id)
        )
        result = await self.db.execute(query)
        purchases_list = result.mappings().all()
        return [self._build_purchase_with_user_and_supply(purchase_data) for purchase_data in purchases_list]

    async def create(
        self,
        user_id: UUID,
        data: PurchaseCreateValueObject,
    ) -> PurchaseEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        kws.pop("user_id", None)  # user_id is passed separately
        query = (
            insert(Purchase)
            .values(
                **kws,
                user_id=user_id,
                tenant_id=self._tenant_id,
            )
            .returning(Purchase.id)
        )
        result = await self.db.execute(query)
        purchase_id = result.scalar_one()
        new_entity = await self.get_by_id(purchase_id)
        self._audit_create("purchase", purchase_id, kws)
        return new_entity  # type: ignore[return-value]

    async def update_data(
        self,
        id: UUID,
        amount: float,
        price: float,
        purchase_date: date,
        unit_price: float,
        unit_of_measurement: UnitOfMeasurement,
    ) -> None:
        # Capture old values before update
        old_row = await self.db.execute(self._filter_tenant(select(Purchase.__table__).where(Purchase.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        new_values = {
            "amount": amount,
            "price": price,
            "purchase_date": str(purchase_date) if isinstance(purchase_date, date) else purchase_date,
            "unit_price": unit_price,
            "unit_of_measurement": unit_of_measurement.value if hasattr(unit_of_measurement, "value") else str(unit_of_measurement),
        }
        query = self._filter_tenant(
            update(Purchase)
            .where(Purchase.id == id)
            .values(
                amount=amount,
                price=price,
                purchase_date=purchase_date,
                unit_price=unit_price,
                unit_of_measurement=unit_of_measurement,
                updated_at=func.now(),
            )
        )
        await self.db.execute(query)
        self._audit_update("purchase", id, old_values, new_values)

    async def delete(self, id: UUID) -> None:
        # Capture old values before delete
        old_row = await self.db.execute(self._filter_tenant(select(Purchase.__table__).where(Purchase.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        query = self._filter_tenant(delete(Purchase).where(Purchase.id == id))
        await self.db.execute(query)
        self._audit_delete("purchase", id, old_values)

    def _build_purchase_with_user_and_supply(self, purchase_data: RowMapping) -> PurchaseEntity:
        return PurchaseEntity(
            id=purchase_data["id"],
            tenant_id=purchase_data["tenant_id"],
            amount=purchase_data["amount"],
            price=purchase_data["price"],
            purchase_date=purchase_data["purchase_date"],
            unit_price=purchase_data["unit_price"],
            unit_of_measurement=purchase_data["unit_of_measurement"],
            user_id=purchase_data["user_id"],
            user_name=purchase_data["user_name"],
            supply_id=purchase_data["supply_id"],
            supply_name=purchase_data["supply_name"],
        )
