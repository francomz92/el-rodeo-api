"""Tests for Celery billing tasks (PR 5 tasks 5.3 & 5.4).

Tests
-----
- expire_trials_task with MockUoW + MockSubscriptionRepository
- monthly_billing_task with MockUoW + mocked MercadoPagoService
- Edge cases: no expired trials, no subscriptions near period end,
  MP error during preference creation

Strategy
--------
Each task uses ``asyncio.run(_run())`` internally.  We patch module-level
dependencies (``AsyncSessionMaker``, ``UnitOfWork``, ``PlanRepository``,
``MercadoPagoHttpClient``) so the inner coroutine executes against mocks.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.billing.domain.entities._feature import Feature
from src.billing.domain.entities._plan import Plan
from src.billing.domain.entities._plan_type import PlanType
from src.billing.domain.entities._quota import Quota
from src.billing.domain.entities._subscription import Subscription
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.repositories import (
    IPaymentRepository,
    ISubscriptionRepository,
    PreferenceResult,
)
from src.billing.domain.value_objects._money import Money

# ── Fixtures ─────────────────────────────────────────────────────────────────


def now() -> datetime:
    return datetime.now(timezone.utc)


def uuid() -> str:
    return str(uuid4())


@pytest.fixture
def free_plan() -> Plan:
    return Plan(
        id=uuid4(),
        plan_type=PlanType.FREE,
        name="Free",
        description="Gratuito",
        features=[],
        quotas=[Quota(name="animals", limit=50)],
        price_monthly=Money(amount=Decimal("0.00")),
    )


@pytest.fixture
def pro_plan() -> Plan:
    return Plan(
        id=uuid4(),
        plan_type=PlanType.PRO,
        name="Pro",
        description="Plan profesional",
        features=[Feature(name="api_access")],
        quotas=[Quota(name="animals", limit=500)],
        price_monthly=Money(amount=Decimal("15.00")),
    )


def _make_sub(
    *,
    status: SubscriptionStatus = SubscriptionStatus.TRIAL,
    trial_end_delta: int = -1,
    period_end_delta: int | None = None,
) -> Subscription:
    """Helper to construct a Subscription with sensible defaults."""
    return Subscription(
        id=uuid4(),
        tenant_id=uuid4(),
        plan_id=uuid4(),
        status=status,
        current_period_start=now() - timedelta(days=30),
        current_period_end=(now() + timedelta(days=period_end_delta) if period_end_delta is not None else None),
        trial_end=(now() + timedelta(days=trial_end_delta) if trial_end_delta is not None else None),
    )


def _patch_task_deps(mock_session_maker, mock_uow_cls, mock_plan_repo_cls):
    """Configure standard mocks for a billing task call.

    Returns a (mock_uow, sub_repo, payment_repo, plan_repo_instance) tuple
    that callers can further customise.
    """
    mock_session = AsyncMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

    mock_uow = MagicMock()
    mock_uow_cls.return_value = mock_uow
    # commit() is awaited — must be an AsyncMock
    mock_uow.commit = AsyncMock()

    sub_repo = MagicMock()
    payment_repo = MagicMock()
    plan_repo_instance = MagicMock()

    def _get_repo(repo_type):
        if repo_type is ISubscriptionRepository:
            return sub_repo
        if repo_type is IPaymentRepository:
            return payment_repo
        return MagicMock()

    mock_uow.get_repository = MagicMock(side_effect=_get_repo)

    mock_plan_repo_cls.return_value = plan_repo_instance

    return mock_uow, sub_repo, payment_repo, plan_repo_instance


# ═══════════════════════════════════════════════════════════════════════════════
# 5.3  expire_trials_task
# ═══════════════════════════════════════════════════════════════════════════════


class TestExpireTrialsTask:
    """Task 5.3 — expire_trials_task tests."""

    EXPIRE_MODULE = "src.billing.infrastructure.workers._expire_trials_task"

    @patch("{}.AsyncSessionMaker".format(EXPIRE_MODULE))
    @patch("{}.UnitOfWork".format(EXPIRE_MODULE))
    @patch("{}.PlanRepository".format(EXPIRE_MODULE))
    def test_expires_expired_trials(
        self,
        mock_plan_repo_cls: MagicMock,
        mock_uow_cls: MagicMock,
        mock_session_maker: MagicMock,
        free_plan: Plan,
    ):
        """Should transition TRIAL → EXPIRED and assign FREE plan."""
        from src.billing.infrastructure.workers._expire_trials_task import expire_trials_task

        _, sub_repo, _payment_repo, plan_repo_instance = _patch_task_deps(mock_session_maker, mock_uow_cls, mock_plan_repo_cls)
        plan_repo_instance.get_by_plan_type = AsyncMock(return_value=free_plan)

        expired = _make_sub(status=SubscriptionStatus.TRIAL, trial_end_delta=-1)
        sub_repo.list_expired_trials = AsyncMock(return_value=[expired])
        sub_repo.update = AsyncMock()

        result = expire_trials_task()

        assert result == {"processed": 1, "succeeded": 1, "failed": 0}
        sub_repo.update.assert_awaited_once()
        updated = sub_repo.update.await_args.args[0]
        assert updated.status == SubscriptionStatus.EXPIRED
        assert updated.plan_id == free_plan.id

    @patch("{}.AsyncSessionMaker".format(EXPIRE_MODULE))
    @patch("{}.UnitOfWork".format(EXPIRE_MODULE))
    @patch("{}.PlanRepository".format(EXPIRE_MODULE))
    def test_no_expired_trials_returns_empty(
        self,
        mock_plan_repo_cls: MagicMock,
        mock_uow_cls: MagicMock,
        mock_session_maker: MagicMock,
        free_plan: Plan,
    ):
        """Should return zeroes when no expired trials exist."""
        from src.billing.infrastructure.workers._expire_trials_task import expire_trials_task

        _, sub_repo, _payment_repo, plan_repo_instance = _patch_task_deps(mock_session_maker, mock_uow_cls, mock_plan_repo_cls)
        plan_repo_instance.get_by_plan_type = AsyncMock(return_value=free_plan)
        sub_repo.list_expired_trials = AsyncMock(return_value=[])

        result = expire_trials_task()

        assert result == {"processed": 0, "succeeded": 0, "failed": 0}
        sub_repo.update.assert_not_called()

    @patch("{}.AsyncSessionMaker".format(EXPIRE_MODULE))
    @patch("{}.UnitOfWork".format(EXPIRE_MODULE))
    @patch("{}.PlanRepository".format(EXPIRE_MODULE))
    def test_active_trials_not_affected(
        self,
        mock_plan_repo_cls: MagicMock,
        mock_uow_cls: MagicMock,
        mock_session_maker: MagicMock,
        free_plan: Plan,
    ):
        """Should skip subscriptions whose trial_end is still in the future."""
        from src.billing.infrastructure.workers._expire_trials_task import expire_trials_task

        _, sub_repo, _payment_repo, plan_repo_instance = _patch_task_deps(mock_session_maker, mock_uow_cls, mock_plan_repo_cls)
        plan_repo_instance.get_by_plan_type = AsyncMock(return_value=free_plan)
        sub_repo.list_expired_trials = AsyncMock(return_value=[])

        result = expire_trials_task()

        assert result == {"processed": 0, "succeeded": 0, "failed": 0}

    @patch("{}.AsyncSessionMaker".format(EXPIRE_MODULE))
    @patch("{}.UnitOfWork".format(EXPIRE_MODULE))
    @patch("{}.PlanRepository".format(EXPIRE_MODULE))
    def test_handles_update_error_gracefully(
        self,
        mock_plan_repo_cls: MagicMock,
        mock_uow_cls: MagicMock,
        mock_session_maker: MagicMock,
        free_plan: Plan,
    ):
        """Should count as failed when update raises."""
        from src.billing.infrastructure.workers._expire_trials_task import expire_trials_task

        _, sub_repo, _payment_repo, plan_repo_instance = _patch_task_deps(mock_session_maker, mock_uow_cls, mock_plan_repo_cls)
        plan_repo_instance.get_by_plan_type = AsyncMock(return_value=free_plan)

        expired = _make_sub(status=SubscriptionStatus.TRIAL, trial_end_delta=-1)
        sub_repo.list_expired_trials = AsyncMock(return_value=[expired])
        sub_repo.update = AsyncMock(side_effect=ValueError("DB error"))

        result = expire_trials_task()

        assert result == {"processed": 1, "succeeded": 0, "failed": 1}


# ═══════════════════════════════════════════════════════════════════════════════
# 5.4  monthly_billing_task
# ═══════════════════════════════════════════════════════════════════════════════


class TestMonthlyBillingTask:
    """Task 5.4 — monthly_billing_task tests."""

    MONTHLY_MODULE = "src.billing.infrastructure.workers._monthly_billing_task"

    @patch("{}.AsyncSessionMaker".format(MONTHLY_MODULE))
    @patch("{}.UnitOfWork".format(MONTHLY_MODULE))
    @patch("{}.PlanRepository".format(MONTHLY_MODULE))
    @patch("{}.MercadoPagoHttpClient".format(MONTHLY_MODULE))
    def test_creates_preferences_for_active_near_end(
        self,
        mock_mp_cls: MagicMock,
        mock_plan_repo_cls: MagicMock,
        mock_uow_cls: MagicMock,
        mock_session_maker: MagicMock,
        pro_plan: Plan,
    ):
        """Should create MP preference and persist PENDING payment."""
        from src.billing.infrastructure.workers._monthly_billing_task import monthly_billing_task

        _, sub_repo, payment_repo, plan_repo_instance = _patch_task_deps(mock_session_maker, mock_uow_cls, mock_plan_repo_cls)

        mock_gateway = MagicMock()
        mock_mp_cls.return_value = mock_gateway
        mock_gateway.create_preference = AsyncMock(
            return_value=PreferenceResult(
                id="pref-999",
                init_point="https://mp.com/checkout/pref-999",
            )
        )

        active_sub = _make_sub(status=SubscriptionStatus.ACTIVE, period_end_delta=3)
        plan_repo_instance.get_by_id = AsyncMock(return_value=pro_plan)
        sub_repo.list_active_near_period_end = AsyncMock(return_value=[active_sub])
        payment_repo.create = AsyncMock()

        mock_uow = mock_uow_cls.return_value
        mock_uow.commit = AsyncMock()

        result = monthly_billing_task()

        assert result == {"processed": 1, "succeeded": 1, "failed": 0}

        # Verify gateway called
        mock_gateway.create_preference.assert_awaited_once()
        call_kwargs = mock_gateway.create_preference.await_args.kwargs
        assert call_kwargs["items"][0].unit_price == Decimal("15.00")
        assert call_kwargs["external_reference"] == f"{active_sub.tenant_id}:{PlanType.PRO.value}"

        # Verify payment persisted
        payment_repo.create.assert_awaited_once()
        payment = payment_repo.create.await_args.args[0]
        assert payment.mp_preference_id == "pref-999"
        assert payment.amount == Decimal("15.00")

    @patch("{}.AsyncSessionMaker".format(MONTHLY_MODULE))
    @patch("{}.UnitOfWork".format(MONTHLY_MODULE))
    @patch("{}.PlanRepository".format(MONTHLY_MODULE))
    @patch("{}.MercadoPagoHttpClient".format(MONTHLY_MODULE))
    def test_no_subs_near_end_returns_empty(
        self,
        mock_mp_cls: MagicMock,
        mock_plan_repo_cls: MagicMock,
        mock_uow_cls: MagicMock,
        mock_session_maker: MagicMock,
    ):
        """Should return zeroes when no subscriptions are near period end."""
        from src.billing.infrastructure.workers._monthly_billing_task import monthly_billing_task

        _, sub_repo, _payment_repo, plan_repo_instance = _patch_task_deps(mock_session_maker, mock_uow_cls, mock_plan_repo_cls)
        mock_gateway = MagicMock()
        mock_mp_cls.return_value = mock_gateway
        sub_repo.list_active_near_period_end = AsyncMock(return_value=[])

        result = monthly_billing_task()
        assert result == {"processed": 0, "succeeded": 0, "failed": 0}

    @patch("{}.AsyncSessionMaker".format(MONTHLY_MODULE))
    @patch("{}.UnitOfWork".format(MONTHLY_MODULE))
    @patch("{}.PlanRepository".format(MONTHLY_MODULE))
    @patch("{}.MercadoPagoHttpClient".format(MONTHLY_MODULE))
    def test_handles_mp_error_gracefully(
        self,
        mock_mp_cls: MagicMock,
        mock_plan_repo_cls: MagicMock,
        mock_uow_cls: MagicMock,
        mock_session_maker: MagicMock,
        pro_plan: Plan,
    ):
        """Should count as failed when MP gateway raises."""
        from src.billing.infrastructure.workers._monthly_billing_task import monthly_billing_task

        _, sub_repo, payment_repo, plan_repo_instance = _patch_task_deps(mock_session_maker, mock_uow_cls, mock_plan_repo_cls)

        mock_gateway = MagicMock()
        mock_mp_cls.return_value = mock_gateway
        mock_gateway.create_preference = AsyncMock(side_effect=ValueError("MP API error"))

        active_sub = _make_sub(status=SubscriptionStatus.ACTIVE, period_end_delta=3)
        plan_repo_instance.get_by_id = AsyncMock(return_value=pro_plan)
        sub_repo.list_active_near_period_end = AsyncMock(return_value=[active_sub])

        mock_uow = mock_uow_cls.return_value
        mock_uow.commit = AsyncMock()

        result = monthly_billing_task()

        assert result == {"processed": 1, "succeeded": 0, "failed": 1}
        payment_repo.create.assert_not_called()

    @patch("{}.AsyncSessionMaker".format(MONTHLY_MODULE))
    @patch("{}.UnitOfWork".format(MONTHLY_MODULE))
    @patch("{}.PlanRepository".format(MONTHLY_MODULE))
    @patch("{}.MercadoPagoHttpClient".format(MONTHLY_MODULE))
    def test_skips_free_plan_subscriptions(
        self,
        mock_mp_cls: MagicMock,
        mock_plan_repo_cls: MagicMock,
        mock_uow_cls: MagicMock,
        mock_session_maker: MagicMock,
        free_plan: Plan,
    ):
        """Should skip subscriptions with zero/no price plans."""
        from src.billing.infrastructure.workers._monthly_billing_task import monthly_billing_task

        _, sub_repo, payment_repo, plan_repo_instance = _patch_task_deps(mock_session_maker, mock_uow_cls, mock_plan_repo_cls)
        mock_gateway = MagicMock()
        mock_mp_cls.return_value = mock_gateway

        active_sub = _make_sub(status=SubscriptionStatus.ACTIVE, period_end_delta=3)
        plan_repo_instance.get_by_id = AsyncMock(return_value=free_plan)
        sub_repo.list_active_near_period_end = AsyncMock(return_value=[active_sub])

        mock_uow = mock_uow_cls.return_value
        mock_uow.commit = AsyncMock()

        result = monthly_billing_task()

        # FREE plans are counted as "succeeded" (no action needed)
        assert result == {"processed": 1, "succeeded": 1, "failed": 0}
        mock_gateway.create_preference.assert_not_called()
        payment_repo.create.assert_not_called()

    @patch("{}.AsyncSessionMaker".format(MONTHLY_MODULE))
    @patch("{}.UnitOfWork".format(MONTHLY_MODULE))
    @patch("{}.PlanRepository".format(MONTHLY_MODULE))
    @patch("{}.MercadoPagoHttpClient".format(MONTHLY_MODULE))
    def test_handles_missing_plan_gracefully(
        self,
        mock_mp_cls: MagicMock,
        mock_plan_repo_cls: MagicMock,
        mock_uow_cls: MagicMock,
        mock_session_maker: MagicMock,
    ):
        """Should count as failed when a subscription's plan is not found."""
        from src.billing.infrastructure.workers._monthly_billing_task import monthly_billing_task

        _, sub_repo, _payment_repo, plan_repo_instance = _patch_task_deps(mock_session_maker, mock_uow_cls, mock_plan_repo_cls)
        mock_gateway = MagicMock()
        mock_mp_cls.return_value = mock_gateway

        active_sub = _make_sub(status=SubscriptionStatus.ACTIVE, period_end_delta=3)
        plan_repo_instance.get_by_id = AsyncMock(return_value=None)
        sub_repo.list_active_near_period_end = AsyncMock(return_value=[active_sub])

        mock_uow = mock_uow_cls.return_value
        mock_uow.commit = AsyncMock()

        result = monthly_billing_task()

        assert result == {"processed": 1, "succeeded": 0, "failed": 1}
        mock_gateway.create_preference.assert_not_called()
