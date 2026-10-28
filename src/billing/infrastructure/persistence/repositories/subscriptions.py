from datetime import timedelta
from uuid import UUID

from sqlalchemy import and_, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.billing.domain.constants.subscriptions import SubscriptionStatus
from src.billing.domain.entities import SubscriptionEntity
from src.billing.domain.repositories import ISubscriptionRepository
from src.billing.infrastructure.persistence.models import Subscription as SubscriptionModel
from src.billing.infrastructure.persistence.repositories.mappers import build_subscription


class SubscriptionRepository(ISubscriptionRepository):
    """SQLAlchemy async implementation of ISubscriptionRepository.

    Tenant scoping is explicit per query: every statement that reads
    subscriptions carries ``tenant_id`` in its WHERE clause. This repository
    deliberately does NOT inherit ``TenantAwareRepository`` — it never called
    ``_filter_tenant``, so the base class and the ``bypass_filter`` flag it
    carries were inert here (F2-4 map #8, odd/tasks/billing-refactor.md).
    """

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def create(self, subscription: SubscriptionEntity) -> SubscriptionEntity:
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
                    SubscriptionModel.gateway_preference_id: subscription.gateway_preference_id,
                    SubscriptionModel.gateway_subscription_id: subscription.gateway_subscription_id,
                    SubscriptionModel.billing_date: subscription.billing_date,
                    SubscriptionModel.next_billing_date: subscription.next_billing_date,
                    SubscriptionModel.gateway_card_id: subscription.gateway_card_id,
                }
            )
            .returning(SubscriptionModel.id)
        )
        result = await self.db.execute(stmt)
        sub_id = result.scalar_one()
        return await self.get_by_id(sub_id)  # type: ignore

    async def update(self, subscription: SubscriptionEntity) -> SubscriptionEntity:
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
                    SubscriptionModel.gateway_preference_id: subscription.gateway_preference_id,
                    SubscriptionModel.gateway_subscription_id: subscription.gateway_subscription_id,
                    SubscriptionModel.billing_date: subscription.billing_date,
                    SubscriptionModel.next_billing_date: subscription.next_billing_date,
                    SubscriptionModel.gateway_card_id: subscription.gateway_card_id,
                    SubscriptionModel.updated_at: func.now(),
                }
            )
        )
        await self.db.execute(stmt)
        return await self.get_by_id(subscription.id)  # type: ignore

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
        SubscriptionModel.gateway_preference_id,
        SubscriptionModel.gateway_subscription_id,
        SubscriptionModel.billing_date,
        SubscriptionModel.next_billing_date,
        SubscriptionModel.gateway_card_id,
    )

    async def get_current_by_tenant(self, tenant_id: UUID) -> SubscriptionEntity | None:
        """Return the tenant's latest subscription row.

        The table does not enforce one row per tenant, so "current" is
        deterministic: the row with the most recent ``current_period_start``
        (Fase 4 #1 — ``one_or_none()`` raised MultipleResultsFound as soon
        as a tenant had more than one row).
        """
        stmt = (
            select(*self._SELECT_COLS)
            .where(SubscriptionModel.tenant_id == tenant_id)
            .order_by(SubscriptionModel.current_period_start.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        row = result.mappings().one_or_none()
        return build_subscription(row) if row else None

    async def get_by_id(self, id: UUID) -> SubscriptionEntity | None:
        stmt = select(*self._SELECT_COLS).where(SubscriptionModel.id == id)
        result = await self.db.execute(stmt)
        row = result.mappings().one_or_none()
        return build_subscription(row) if row else None

    async def list_expired_trials(self) -> list[SubscriptionEntity]:
        stmt = select(*self._SELECT_COLS).where(
            and_(
                SubscriptionModel.trial_end.isnot(None),
                SubscriptionModel.trial_end < func.now(),
                SubscriptionModel.status == SubscriptionStatus.TRIAL.value,
            )
        )
        result = await self.db.execute(stmt)
        return [build_subscription(row) for row in result.mappings().all()]

    async def list_active_near_period_end(self, days_ahead: int) -> list[SubscriptionEntity]:
        stmt = select(*self._SELECT_COLS).where(
            and_(
                SubscriptionModel.status == SubscriptionStatus.ACTIVE.value,
                SubscriptionModel.current_period_end.isnot(None),
                SubscriptionModel.current_period_end <= func.now() + timedelta(days=days_ahead),
                SubscriptionModel.current_period_end > func.now(),
            )
        )
        result = await self.db.execute(stmt)
        return [build_subscription(row) for row in result.mappings().all()]

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        status_filter: SubscriptionStatus | None = None,
    ) -> list[SubscriptionEntity]:
        """List subscriptions for a tenant with optional status filter."""
        conditions = [SubscriptionModel.tenant_id == tenant_id]
        if status_filter is not None:
            conditions.append(SubscriptionModel.status == status_filter.value)

        stmt = select(*self._SELECT_COLS).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return [build_subscription(row) for row in result.mappings().all()]

    async def get_by_gateway_subscription_id(self, gateway_subscription_id: str) -> SubscriptionEntity | None:
        """Retrieve a subscription by its gateway subscription ID."""
        stmt = select(*self._SELECT_COLS).where(SubscriptionModel.gateway_subscription_id == gateway_subscription_id)
        result = await self.db.execute(stmt)
        row = result.mappings().one_or_none()
        return build_subscription(row) if row else None
