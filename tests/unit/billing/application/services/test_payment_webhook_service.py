"""Tests for PaymentWebhookService — specifically that PaymentReceived
is dispatched when a payment is approved.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.billing.application.services._payment_webhook_service import (
    PaymentWebhookService,
)
from src.billing.domain.entities._payment_status import PaymentStatus
from src.billing.domain.entities._plan_type import PlanType
from src.billing.domain.entities._subscription import Subscription
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.repositories import (
    IPaymentGateway,
    IPaymentRepository,
    IPlanRepository,
    ISubscriptionRepository,
)
from src.common.application.ports.email_notifier import IEmailNotifier
from src.common.application.ports.uow import IUoW, IUoWFactory


class _FakeUoW(IUoW):
    """Fake UoW that delegates get_repository to a dict and tracks commit."""

    def __init__(self, repos: dict) -> None:
        super().__init__()
        self._repos = repos
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def get_repository(self, repository_type):
        repo = self._repos.get(repository_type)
        if repo is None:
            raise ValueError(f"No mock repo for {repository_type}")
        return repo

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True

    async def refresh(self, entity):
        pass

    async def dispose(self):
        pass

    def add_before_commit_hook(self, hook):
        pass

    def add_outbox_event(self, event):
        pass


class _FakeUoWFactory(IUoWFactory):
    """Factory that returns a pre-configured _FakeUoW."""

    def __init__(self, repos: dict) -> None:
        self._repos = repos

    def __call__(self) -> IUoW:
        return _FakeUoW(self._repos)


class TestPaymentWebhookService:
    """PaymentWebhookService dispatches PaymentReceived on APPROVED."""

    def setup_method(self) -> None:
        self.tenant_id = uuid4()
        self.subscription_id = uuid4()
        self.mp_payment_id = "mp-12345"
        self.plan_id = uuid4()

        self.gateway = MagicMock(spec=IPaymentGateway)
        self.gateway.validate_signature = MagicMock(return_value=True)
        self.plan_repo = MagicMock(spec=IPlanRepository)
        self.notifier = MagicMock(spec=IEmailNotifier)

        # Mock repositories that will live inside the fake UoW
        self.payment_repo = MagicMock()
        self.subscription_repo = MagicMock()
        self.user_repo = MagicMock()

        repos = {
            IPaymentRepository: self.payment_repo,
            ISubscriptionRepository: self.subscription_repo,
            IUserRepository: self.user_repo,
        }
        uow_factory = _FakeUoWFactory(repos)

        self.service = PaymentWebhookService(
            gateway=self.gateway,
            plan_repo=self.plan_repo,
            uow_factory=uow_factory,
            email_notifier=self.notifier,
        )

        # Pre-configure user_repo.list so the email handlers don't crash
        self.user_repo.list = AsyncMock(return_value=([], 0, False))

    def _now(self) -> datetime:
        return datetime.now(tz=timezone.utc)

    def _setup_approved_payment_mocks(self) -> None:
        """Configure mocks for an APPROVED payment flow."""
        self.payment_repo.get_by_mp_payment_id = AsyncMock(return_value=None)

        payment_result = MagicMock()
        payment_result.external_reference = f"{self.tenant_id}:enterprise"
        payment_result.transaction_amount = Decimal("99.99")
        payment_result.status = PaymentStatus.APPROVED
        payment_result.id = "pref-001"
        self.gateway.get_payment = AsyncMock(return_value=payment_result)

        # Use a real Subscription (frozen dataclass) — required by replace()
        sub = Subscription(
            id=self.subscription_id,
            tenant_id=self.tenant_id,
            plan_id=self.plan_id,
            status=SubscriptionStatus.TRIAL,
            current_period_start=self._now() - timedelta(days=30),
            current_period_end=datetime(2025, 7, 15, tzinfo=timezone.utc),
        )
        self.subscription_repo.get_by_tenant = AsyncMock(return_value=sub)
        self.subscription_repo.get_by_id = AsyncMock(return_value=sub)

        # plan_repo.get_by_plan_type returns the enterprise plan for the external_ref
        enterprise_plan = MagicMock()
        enterprise_plan.id = uuid4()
        enterprise_plan.plan_type = PlanType.ENTERPRISE
        self.plan_repo.get_by_plan_type = AsyncMock(return_value=enterprise_plan)

        self.payment_repo.create = AsyncMock()
        self.subscription_repo.update = AsyncMock()

        owner = MagicMock()
        owner.name = "Juan Pérez"
        owner.email = "juan@ejemplo.com"
        self.user_repo.list = AsyncMock(return_value=([owner], 1, False))

    @pytest.mark.asyncio
    async def test_dispatches_payment_received_on_approved(self) -> None:
        """PaymentReceived is dispatched when payment status is APPROVED."""
        self._setup_approved_payment_mocks()

        await self.service.handle_ipn(
            topic="payment",
            id=self.mp_payment_id,
            x_signature="ts=123|v1=valid",
            x_request_id="req-abc",
        )

        self.payment_repo.create.assert_called_once()
        self.subscription_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_not_dispatch_on_rejected(self) -> None:
        """PaymentReceived is NOT dispatched when payment is rejected."""
        self.payment_repo.get_by_mp_payment_id = AsyncMock(return_value=None)

        payment_result = MagicMock()
        payment_result.external_reference = f"{self.tenant_id}:enterprise"
        payment_result.transaction_amount = Decimal("50.00")
        payment_result.status = PaymentStatus.REJECTED
        payment_result.id = "pay-rejected-001"
        self.gateway.get_payment = AsyncMock(return_value=payment_result)

        # Use a real Subscription (frozen dataclass) — required by replace()
        sub = Subscription(
            id=self.subscription_id,
            tenant_id=self.tenant_id,
            plan_id=self.plan_id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=self._now() - timedelta(days=15),
            current_period_end=self._now() + timedelta(days=15),
        )
        self.subscription_repo.get_by_tenant = AsyncMock(return_value=sub)
        self.subscription_repo.get_by_id = AsyncMock(return_value=sub)
        self.payment_repo.create = AsyncMock()
        self.subscription_repo.update = AsyncMock()

        await self.service.handle_ipn(
            topic="payment",
            id=self.mp_payment_id,
            x_signature="ts=123|v1=valid",
            x_request_id="req-abc",
        )

        self.payment_repo.create.assert_called_once()
        self.subscription_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_not_dispatch_on_idempotent_duplicate(self) -> None:
        """PaymentReceived is NOT dispatched when payment already exists."""
        existing = MagicMock()
        self.payment_repo.get_by_mp_payment_id = AsyncMock(return_value=existing)

        await self.service.handle_ipn(
            topic="payment",
            id=self.mp_payment_id,
            x_signature="ts=123|v1=valid",
            x_request_id="req-abc",
        )

        self.gateway.get_payment.assert_not_called()
        self.payment_repo.create.assert_not_called()


class TestPaymentWebhookFrozenDataclass:
    """Webhook uses dataclasses.replace() — not direct mutation — on frozen Subscription.

    The ``Subscription`` entity is a frozen dataclass.  Direct assignment like
    ``sub.status = X`` raises ``FrozenInstanceError``.  The handler MUST use
    ``dataclasses.replace(sub, status=X, ...)`` instead.
    """

    def setup_method(self) -> None:
        self.tenant_id = uuid4()
        self.subscription_id = uuid4()
        self.plan_id = uuid4()
        self.new_plan_id = uuid4()
        self.mp_payment_id = "mp-12345"

        self.gateway = MagicMock(spec=IPaymentGateway)
        self.gateway.validate_signature = MagicMock(return_value=True)
        self.plan_repo = MagicMock(spec=IPlanRepository)
        self.notifier = MagicMock(spec=IEmailNotifier)

        self.payment_repo = MagicMock()
        self.subscription_repo = MagicMock()
        self.user_repo = MagicMock()

        repos = {
            IPaymentRepository: self.payment_repo,
            ISubscriptionRepository: self.subscription_repo,
            IUserRepository: self.user_repo,
        }
        uow_factory = _FakeUoWFactory(repos)

        self.service = PaymentWebhookService(
            gateway=self.gateway,
            plan_repo=self.plan_repo,
            uow_factory=uow_factory,
            email_notifier=self.notifier,
        )

        # Pre-configure user_repo.list as async so the email handler doesn't crash
        self.user_repo.list = AsyncMock(return_value=([], 0, False))

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _build_real_sub(self, **overrides: object) -> Subscription:
        """Build a real (frozen) Subscription with sensible defaults."""
        defaults: dict = {
            "id": self.subscription_id,
            "tenant_id": self.tenant_id,
            "plan_id": self.plan_id,
            "status": SubscriptionStatus.TRIAL,
            "current_period_start": self._now() - timedelta(days=30),
            "current_period_end": self._now() + timedelta(days=1),
        }
        defaults.update(overrides)
        return Subscription(**defaults)  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_approved_payment_uses_dataclass_replace(self) -> None:
        """APPROVED payment uses replace() which works on frozen dataclass."""
        self.payment_repo.get_by_mp_payment_id = AsyncMock(return_value=None)

        payment_result = MagicMock()
        payment_result.external_reference = f"{self.tenant_id}:pro"
        payment_result.transaction_amount = Decimal("99.99")
        payment_result.status = PaymentStatus.APPROVED
        payment_result.id = "pref-001"
        self.gateway.get_payment = AsyncMock(return_value=payment_result)

        real_sub = self._build_real_sub()
        self.subscription_repo.get_by_tenant = AsyncMock(return_value=real_sub)
        self.subscription_repo.get_by_id = AsyncMock(return_value=real_sub)
        self.payment_repo.create = AsyncMock()
        self.subscription_repo.update = AsyncMock()

        plan = MagicMock()
        plan.plan_type = PlanType.PRO
        self.plan_repo.get_by_id = AsyncMock(return_value=plan)

        # Act
        await self.service.handle_ipn(
            topic="payment",
            id=self.mp_payment_id,
            x_signature="ts=123|v1=valid",
            x_request_id="req-abc",
        )

        # Assert: update was called with a modified copy, not direct mutation
        self.subscription_repo.update.assert_called_once()
        updated_sub = self.subscription_repo.update.await_args.args[0]
        assert updated_sub.status == SubscriptionStatus.ACTIVE
        assert updated_sub is not real_sub  # Different object (replace() creates copy)

    @pytest.mark.asyncio
    async def test_subscription_becomes_active_on_approved(self) -> None:
        """Subscription status becomes ACTIVE after APPROVED payment."""
        self.payment_repo.get_by_mp_payment_id = AsyncMock(return_value=None)

        payment_result = MagicMock()
        payment_result.external_reference = f"{self.tenant_id}:pro"
        payment_result.transaction_amount = Decimal("99.99")
        payment_result.status = PaymentStatus.APPROVED
        payment_result.id = "pref-001"
        self.gateway.get_payment = AsyncMock(return_value=payment_result)

        real_sub = self._build_real_sub()
        self.subscription_repo.get_by_tenant = AsyncMock(return_value=real_sub)
        self.subscription_repo.get_by_id = AsyncMock(return_value=real_sub)
        self.payment_repo.create = AsyncMock()
        self.subscription_repo.update = AsyncMock()

        plan = MagicMock()
        plan.plan_type = PlanType.PRO
        self.plan_repo.get_by_id = AsyncMock(return_value=plan)

        await self.service.handle_ipn(
            topic="payment",
            id=self.mp_payment_id,
            x_signature="ts=123|v1=valid",
            x_request_id="req-abc",
        )

        updated = self.subscription_repo.update.await_args.args[0]
        assert updated.status == SubscriptionStatus.ACTIVE
        assert updated.current_period_start is not None
        assert updated.current_period_end is not None
        assert updated.gateway_preference_id == "pref-001"

    @pytest.mark.asyncio
    async def test_upgrade_changes_plan_id_from_external_reference(self) -> None:
        """Upgrade scenario parses plan_type from external_reference and updates plan_id."""
        self.payment_repo.get_by_mp_payment_id = AsyncMock(return_value=None)

        payment_result = MagicMock()
        # external_reference format: "{tenant_id}:{plan_type}"
        payment_result.external_reference = f"{self.tenant_id}:enterprise"
        payment_result.transaction_amount = Decimal("299.99")
        payment_result.status = PaymentStatus.APPROVED
        payment_result.id = "pref-002"
        self.gateway.get_payment = AsyncMock(return_value=payment_result)

        # Current subscription is on FREE plan
        real_sub = self._build_real_sub(plan_id=self.plan_id)
        self.subscription_repo.get_by_tenant = AsyncMock(return_value=real_sub)
        self.subscription_repo.get_by_id = AsyncMock(return_value=real_sub)
        self.payment_repo.create = AsyncMock()
        self.subscription_repo.update = AsyncMock()

        # The plan repo resolves the ENTERPRISE plan by plan_type
        enterprise_plan = MagicMock()
        enterprise_plan.id = self.new_plan_id
        enterprise_plan.plan_type = PlanType.ENTERPRISE
        self.plan_repo.get_by_id = AsyncMock(return_value=enterprise_plan)

        # plan_repo.get_by_plan_type returns the enterprise plan
        self.plan_repo.get_by_plan_type = AsyncMock(return_value=enterprise_plan)

        await self.service.handle_ipn(
            topic="payment",
            id=self.mp_payment_id,
            x_signature="ts=123|v1=valid",
            x_request_id="req-abc",
        )

        updated = self.subscription_repo.update.await_args.args[0]
        assert updated.plan_id == self.new_plan_id
        assert updated.status == SubscriptionStatus.ACTIVE
