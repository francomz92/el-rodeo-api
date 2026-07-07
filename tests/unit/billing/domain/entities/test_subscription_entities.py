"""Tests for SubscriptionStatus and Subscription domain entities."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.billing.domain.entities._subscription import Subscription
from src.billing.domain.entities._subscription_status import SubscriptionStatus


class TestSubscriptionStatus:
    """Task 1.6: SubscriptionStatus enum."""

    def test_values(self) -> None:
        assert SubscriptionStatus.TRIAL == "trial"
        assert SubscriptionStatus.ACTIVE == "active"
        assert SubscriptionStatus.CANCELED == "canceled"
        assert SubscriptionStatus.EXPIRED == "expired"
        assert SubscriptionStatus.PAST_DUE == "past_due"

    def test_string_conversion(self) -> None:
        assert str(SubscriptionStatus.TRIAL) == "trial"
        assert str(SubscriptionStatus.ACTIVE) == "active"
        assert str(SubscriptionStatus.CANCELED) == "canceled"
        assert str(SubscriptionStatus.EXPIRED) == "expired"
        assert str(SubscriptionStatus.PAST_DUE) == "past_due"

    def test_membership(self) -> None:
        assert SubscriptionStatus("trial") is SubscriptionStatus.TRIAL
        assert SubscriptionStatus("active") is SubscriptionStatus.ACTIVE
        assert SubscriptionStatus("canceled") is SubscriptionStatus.CANCELED
        assert SubscriptionStatus("expired") is SubscriptionStatus.EXPIRED
        assert SubscriptionStatus("past_due") is SubscriptionStatus.PAST_DUE


class TestSubscription:
    """Task 1.7: Subscription dataclass."""

    def test_construct_with_trial(self) -> None:
        sub_id = uuid4()
        tenant_id = uuid4()
        plan_id = uuid4()
        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=14)
        sub = Subscription(
            id=sub_id,
            tenant_id=tenant_id,
            plan_id=plan_id,
            status=SubscriptionStatus.TRIAL,
            current_period_start=now,
            current_period_end=trial_end,
            trial_end=trial_end,
        )
        assert sub.id == sub_id
        assert sub.tenant_id == tenant_id
        assert sub.plan_id == plan_id
        assert sub.status == SubscriptionStatus.TRIAL
        assert sub.current_period_start == now
        assert sub.current_period_end == trial_end
        assert sub.trial_end == trial_end
        assert sub.canceled_at is None
        assert sub.metadata is None

    def test_construct_active(self) -> None:
        sub_id = uuid4()
        tenant_id = uuid4()
        plan_id = uuid4()
        now = datetime.now(timezone.utc)
        period_end = now + timedelta(days=30)
        sub = Subscription(
            id=sub_id,
            tenant_id=tenant_id,
            plan_id=plan_id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            current_period_end=period_end,
        )
        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.trial_end is None
        assert sub.canceled_at is None
        assert sub.current_period_end == period_end

    def test_construct_with_metadata(self) -> None:
        sub_id = uuid4()
        tenant_id = uuid4()
        plan_id = uuid4()
        now = datetime.now(timezone.utc)
        metadata = {"animals_count": 10, "used_storage_mb": 50}
        sub = Subscription(
            id=sub_id,
            tenant_id=tenant_id,
            plan_id=plan_id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            metadata=metadata,
        )
        assert sub.metadata == metadata
