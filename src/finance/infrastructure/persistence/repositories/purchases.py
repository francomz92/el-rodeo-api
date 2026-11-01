from datetime import date
from uuid import UUID

from sqlalchemy import delete, exists, func, insert, select, update

from src.common.application.pagination.cursor import cursor_uuid, decode_cursor
from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)
from src.finance.domain.constants.animal_supplies import UnitOfMeasurement
from src.finance.domain.constants.purchases import PurchaseStatus
from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.value_objects.purchase_value_objects import PurchaseCreateValueObject, PurchaseListQueryParamValueObject
from src.finance.infrastructure.persistence.models import AnimalSupply, Purchase

from .mappers import build_purchase_with_supply


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
                AnimalSupply.name.label("supply_name"),
            )
            .where(Purchase.id == id)
            .outerjoin(AnimalSupply, Purchase.supply_id == AnimalSupply.id)
        )
        result = await self.db.execute(query)
        purchase_db = result.mappings().one_or_none()
        return build_purchase_with_supply(purchase_db) if purchase_db else None

    async def list_for_user(
        self,
        filters: PurchaseListQueryParamValueObject,
        limit: int,
        offset: int,
        order_by: str,
        cursor: str | None = None,
    ) -> tuple[list[PurchaseEntity], int, bool]:
        conditions = []
        for k, v in vars(filters).items():
            if v is Sentinel.UNSET:
                continue
            elif k in (
                "id",
                "supply_id",
                "purchase_date",
                "unit_of_measurement",
                "status",
            ):
                conditions.append(getattr(Purchase, k) == v)

        base_columns = [
            *Purchase.__table__.columns,
            AnimalSupply.name.label("supply_name"),
        ]
        base_join = Purchase.supply_id == AnimalSupply.id

        # ── Explicit order column resolution ────────────────────────
        # A raw string order_by ("id") is ambiguous once the AnimalSupply
        # join enters the FROM clause: ambiguous keyset pages emit the
        # wrong row as the continuation token and the next page comes
        # back empty. Purchases map only the columns that actually exist
        # on this table (the shared catalog also allows "name", which
        # this table has not); anything else falls back to id so sort and
        # keyset stay coherent.
        order_column = {
            "id": Purchase.id,
            "created_at": Purchase.created_at,
            "updated_at": Purchase.updated_at,
        }.get(order_by, Purchase.id)

        # ── Count total (filter-wide, not cursor-sliced) ────────────
        count_query = self._filter_tenant(select(func.count()).select_from(Purchase).where(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # ── Data query ──────────────────────────────────────────────
        if cursor is not None:
            cursor_data = decode_cursor(cursor)
            cursor_id = cursor_uuid(cursor_data)
            # The token carries id + sort_value, but only the id
            # comparison applies here (same limitation as animals).
            query = self._filter_tenant(
                select(*base_columns)
                .where(*conditions, Purchase.id > cursor_id)
                .order_by(order_column)
                .limit(limit + 1)  # fetch one extra to detect next page
                .outerjoin(AnimalSupply, base_join)
            )
        else:
            query = self._filter_tenant(
                select(*base_columns)
                .where(*conditions)
                .limit(limit + 1)
                .offset(offset)
                .order_by(order_column)
                .outerjoin(AnimalSupply, base_join)
            )

        result = await self.db.execute(query)
        purchases_list = result.mappings().all()

        # Both modes fetch one extra row (limit+1) so has_next is always
        # observable — the first page must hand the FE the next_cursor.
        has_next = len(purchases_list) > limit
        if has_next:
            purchases_list = purchases_list[:limit]

        items = [build_purchase_with_supply(purchase_data) for purchase_data in purchases_list]
        return items, total, has_next

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
        return new_entity  # type: ignore

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

    async def mark_confirmed(self, id: UUID, confirmed_by: UUID) -> bool:
        """Transition a pending purchase to confirmed.

        Returns False when the purchase is not in ``pending`` status anymore
        (concurrent confirmation), never mutating stock twice.
        """
        old_row = await self.db.execute(self._filter_tenant(select(Purchase.status).where(Purchase.id == id)))
        old_status = old_row.scalars().first()
        query = self._filter_tenant(
            update(Purchase)
            .where(Purchase.id == id)
            .where(Purchase.status == PurchaseStatus.PENDING)
            .values(
                status=PurchaseStatus.CONFIRMED,
                confirmed_at=func.now(),
                confirmed_by=confirmed_by,
                updated_at=func.now(),
            )
            .returning(Purchase.id)
        )
        result = await self.db.execute(query)
        confirmed = result.scalar_one_or_none() is not None
        if confirmed:
            self._audit_update(
                "purchase", id, {"status": getattr(old_status, "value", old_status)}, {"status": PurchaseStatus.CONFIRMED.value}
            )
        return confirmed
