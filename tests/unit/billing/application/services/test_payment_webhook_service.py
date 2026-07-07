"""Tests for PaymentWebhookService — specifically that PaymentReceived
is dispatched when a payment is approved.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.billing.application.services._payment_webhook_service import (
    PaymentWebhookService,
)
from src.billing.domain.entities._payment_status import PaymentStatus
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.repositories import (
    IPaymentGateway,
    IPaymentRepository,
    ISubscriptionRepository,
)
from src.common.domain.events.base import DomainEvent
from src.common.domain.ports.event_bus import IEventBus


class TestPaymentWebhookService:
    """PaymentWebhookService dispatches PaymentReceived on APPROVED."""

    def setup_method(self) -> None:
        self.tenant_id = uuid4()
        self.subscription_id = uuid4()
        self.mp_payment_id = "mp-12345"

        self.gateway = MagicMock(spec=IPaymentGateway)
        self.gateway.validate_signature = MagicMock(return_value=True)
        self.payment_repo = MagicMock(spec=IPaymentRepository)
        self.subscription_repo = MagicMock(spec=ISubscriptionRepository)
        self.event_bus = MagicMock(spec=IEventBus)

        self.service = PaymentWebhookService(
            gateway=self.gateway,
            payment_repo=self.payment_repo,
            subscription_repo=self.subscription_repo,
            event_bus=self.event_bus,
        )

    def _setup_approved_payment_mocks(self) -> None:
        """Configure mocks for an APPROVED payment flow."""
        # No existing payment (idempotency)
        self.payment_repo.get_by_mp_payment_id = AsyncMock(return_value=None)

        # MP gateway returns approved payment
        payment_result = MagicMock()
        payment_result.external_reference = f"{self.tenant_id}:enterprise"
        payment_result.transaction_amount = Decimal("99.99")
        payment_result.status = PaymentStatus.APPROVED
        payment_result.id = "pref-001"
        self.gateway.get_payment = AsyncMock(return_value=payment_result)

        # Subscription exists
        sub = MagicMock()
        sub.id = self.subscription_id
        sub.status = SubscriptionStatus.TRIAL
        self.subscription_repo.get_by_tenant = AsyncMock(return_value=sub)
        self.subscription_repo.get_by_id = AsyncMock(return_value=sub)

        # Payment repo create
        self.payment_repo.create = AsyncMock()
        self.subscription_repo.update = AsyncMock()

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

        self.event_bus.dispatch.assert_called_once()
        (dispatched_event,) = self.event_bus.dispatch.call_args[0]
        assert isinstance(dispatched_event, DomainEvent)
        assert dispatched_event.event_type == "payment.received"
        assert dispatched_event.aggregate_id is not None

    @pytest.mark.asyncio
    async def test_does_not_dispatch_on_rejected(self) -> None:
        """PaymentReceived is NOT dispatched when payment is rejected."""
        self.payment_repo.get_by_mp_payment_id = AsyncMock(return_value=None)

        payment_result = MagicMock()
        payment_result.external_reference = f"{self.tenant_id}:enterprise"
        payment_result.transaction_amount = Decimal("50.00")
        payment_result.status = PaymentStatus.REJECTED
        self.gateway.get_payment = AsyncMock(return_value=payment_result)

        sub = MagicMock()
        sub.id = self.subscription_id
        sub.status = SubscriptionStatus.ACTIVE
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

        self.event_bus.dispatch.assert_not_called()

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

        self.event_bus.dispatch.assert_not_called()
        self.gateway.get_payment.assert_not_called()
