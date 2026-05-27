from datetime import date
from uuid import UUID

from sqlalchemy import delete, exists, insert, select, update
from sqlalchemy.orm import joinedload

from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories.mixins import SessionMixin
from src.finance.domain.constatns.animal_supplies import UnitOfMeasurement
from src.finance.domain.entities.purchases import PurchaseEntity
from src.finance.domain.repositories.purchases import IPurchasesRepository
from src.finance.domain.value_objetcts.purchase_value_objects import PurchaseCreateValueObject, PurchaseListQueryParamValueObject
from src.finance.infrastructure.persistance.models import Purchase


class PurchasesRepository(IPurchasesRepository, SessionMixin):
    async def exists(self, id: UUID, user_id: UUID) -> bool:
        query = (
            exists(Purchase)
            .where(
                Purchase.id == id,
                Purchase.user_id == user_id,
            )
            .select()
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(
        self,
        id: UUID,
        user_id: UUID,
    ) -> PurchaseEntity | None:
        query = (
            select(Purchase)
            .where(
                Purchase.id == id,
                Purchase.user_id == user_id,
            )
            .options(
                joinedload(Purchase.supplie),
            )
        )
        result = await self.db.execute(query)
        purchase_db = result.scalar_one_or_none()
        return self._build_purchase_with_user_and_supplie(purchase_db) if purchase_db else None

    async def list_for_user(
        self,
        user_id: UUID,
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
        query = (
            select(Purchase)
            .where(
                Purchase.user_id == user_id,
                *conditions,
            )
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
            .options(
                joinedload(Purchase.user),
                joinedload(Purchase.supplie),
            )
        )
        result = await self.db.execute(query)
        purchases_list = result.scalars().unique().all()
        return [self._build_purchase_with_user_and_supplie(purchase_data) for purchase_data in purchases_list]

    async def create(
        self,
        user_id: UUID,
        data: PurchaseCreateValueObject,
    ) -> PurchaseEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        query = (
            insert(Purchase)
            .values(
                **kws,
                user_id=user_id,
            )
            .returning(Purchase.id)
        )
        result = await self.db.execute(query)
        purchase_id = result.scalar_one()
        return self.get_by_id(purchase_id, user_id)  # type: ignore

    async def update_data(
        self,
        id: UUID,
        amount: float,
        price: float,
        purchase_date: date,
        unit_price: float,
        unit_of_measurement: UnitOfMeasurement,
    ) -> None:
        query = (
            update(Purchase)
            .where(Purchase.id == id)
            .values(
                amount=amount,
                price=price,
                purchase_date=purchase_date,
                unit_price=unit_price,
                unit_of_measurement=unit_of_measurement,
            )
        )
        await self.db.execute(query)

    async def delete(self, id: UUID) -> None:
        query = delete(Purchase).where(Purchase.id == id)
        await self.db.execute(query)

    def _build_purchase_with_user_and_supplie(
        self,
        purchase_data: Purchase,
    ) -> PurchaseEntity:
        return PurchaseEntity(
            id=purchase_data.id,
            amount=purchase_data.amount,
            price=purchase_data.price,
            purchase_date=purchase_data.purchase_date,
            unit_price=purchase_data.unit_price,
            unit_of_measurement=purchase_data.unit_of_measurement,
            user=purchase_data.user,
            supplie=purchase_data.supplie,
        )
