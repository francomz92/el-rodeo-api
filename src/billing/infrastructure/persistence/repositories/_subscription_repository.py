from datetime import timedelta
from uuid import UUID

from sqlalchemy import RowMapping, and_, func, insert, select, update

from src.billing.domain.entities._subscription import Subscription
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.repositories import ISubscriptionRepository
from src.billing.infrastructure.persistence.models import Subscription as SubscriptionModel
from src.common.infrastructure.persistence.repositories.mixins import SessionMixin


class SubscriptionRepository(ISubscriptionRepository, SessionMixin):
    async def create(self, subscription: Subscription) -> Subscription:
        stmt = (
            insert(SubscriptionModel)
            .values(
                {
                    SubscriptionModel.id: subscription.id,
                    SubscriptionModel.tenant_id: subscription.tenant_id,
                    SubscriptionModel.plan_id: subscription.plan_id,
                    SubscriptionModel.status: subscription.status.value,
                    SubscriptionModel.current_period_start: subscription.current_period_start,
                    SubscriptionModel.current_period_end: subscription.current_period_end,
                    SubscriptionModel.trial_end: subscription.trial_end,
                    SubscriptionModel.canceled_at: subscription.canceled_at,
                    SubscriptionModel.subscription_metadata: subscription.metadata,
                    SubscriptionModel.mp_preference_id: subscription.mp_preference_id,
                    SubscriptionModel.mp_subscription_id: subscription.mp_subscription_id,
                }
            )
            .returning(SubscriptionModel.id)
        )
        result = await self.db.execute(stmt)
        sub_id = result.scalar_one()
        return await self.get_by_id(sub_id)  # type: ignore[return-value]

    async def update(self, subscription: Subscription) -> Subscription:
        stmt = (
            update(SubscriptionModel)
            .where(SubscriptionModel.id == subscription.id)
            .values(
                {
                    SubscriptionModel.plan_id: subscription.plan_id,
                    SubscriptionModel.status: subscription.status.value,
                    SubscriptionModel.current_period_start: subscription.current_period_start,
                    SubscriptionModel.current_period_end: subscription.current_period_end,
                    SubscriptionModel.trial_end: subscription.trial_end,
                    SubscriptionModel.canceled_at: subscription.canceled_at,
                    SubscriptionModel.subscription_metadata: subscription.metadata,
                    SubscriptionModel.mp_preference_id: subscription.mp_preference_id,
                    SubscriptionModel.mp_subscription_id: subscription.mp_subscription_id,
                    SubscriptionModel.updated_at: func.now(),
                }
            )
        )
        await self.db.execute(stmt)
        return await self.get_by_id(subscription.id)  # type: ignore[return-value]

    _SELECT_COLS = (
        SubscriptionModel.id,
        SubscriptionModel.tenant_id,
        SubscriptionModel.plan_id,
        SubscriptionModel.status,
        SubscriptionModel.current_period_start,
        SubscriptionModel.current_period_end,
        SubscriptionModel.trial_end,
        SubscriptionModel.canceled_at,
        SubscriptionModel.subscription_metadata,
        SubscriptionModel.mp_preference_id,
        SubscriptionModel.mp_subscription_id,
    )

    async def get_by_tenant(self, tenant_id: UUID) -> Subscription | None:
        stmt = select(*self._SELECT_COLS).where(SubscriptionModel.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        row = result.mappings().one_or_none()
        return self._build_entity(row) if row else None

    async def get_by_id(self, id: UUID) -> Subscription | None:
        stmt = select(*self._SELECT_COLS).where(SubscriptionModel.id == id)
        result = await self.db.execute(stmt)
        row = result.mappings().one_or_none()
        return self._build_entity(row) if row else None

    async def list_expired_trials(self) -> list[Subscription]:
        stmt = select(*self._SELECT_COLS).where(
            and_(
                SubscriptionModel.trial_end.isnot(None),
                SubscriptionModel.trial_end < func.now(),
                SubscriptionModel.status == SubscriptionStatus.TRIAL.value,
            )
        )
        result = await self.db.execute(stmt)
        return [self._build_entity(row) for row in result.mappings().all()]

    async def list_active_near_period_end(self, days_ahead: int) -> list[Subscription]:
        stmt = select(*self._SELECT_COLS).where(
            and_(
                SubscriptionModel.status == SubscriptionStatus.ACTIVE.value,
                SubscriptionModel.current_period_end.isnot(None),
                SubscriptionModel.current_period_end <= func.now() + timedelta(days=days_ahead),
                SubscriptionModel.current_period_end > func.now(),
            )
        )
        result = await self.db.execute(stmt)
        return [self._build_entity(row) for row in result.mappings().all()]

    @staticmethod
    def _build_entity(row: RowMapping) -> Subscription:
        return Subscription(
            id=row["id"],
            tenant_id=row["tenant_id"],
            plan_id=row["plan_id"],
            status=SubscriptionStatus(row["status"]),
            current_period_start=row["current_period_start"],
            current_period_end=row.get("current_period_end"),
            trial_end=row.get("trial_end"),
            canceled_at=row.get("canceled_at"),
            metadata=row.get("subscription_metadata"),
            mp_preference_id=row.get("mp_preference_id"),
            mp_subscription_id=row.get("mp_subscription_id"),
        )
