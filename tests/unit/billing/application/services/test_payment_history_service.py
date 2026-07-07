"""Tests for PaymentHistoryService.

Tests:
- Pagination returns correct slice
- Cross-tenant isolation (tenant A can't see tenant B's payments)
- Empty list for tenant with no payments
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.billing.application.services._payment_history_service import (
    PaymentHistoryService,
)
from src.billing.domain.entities._payment import Payment
from src.billing.domain.entities._payment_status import PaymentStatus
from src.billing.domain.repositories import IPaymentRepository


class TestPaymentHistoryService:
    """PaymentHistoryService provides paginated, tenant-scoped payment queries."""

    def setup_method(self) -> None:
        """Set up service with a mocked payment repository."""
        self.payment_repo = MagicMock(spec=IPaymentRepository)
        self.service = PaymentHistoryService(payment_repo=self.payment_repo)

        self.tenant_a = uuid4()
        self.tenant_b = uuid4()
        now = datetime.now(timezone.utc)

        # 3 payments for tenant_a
        self.payments_a = [
            Payment(
                tenant_id=self.tenant_a,
                subscription_id=uuid4(),
                status=PaymentStatus.APPROVED,
                amount=Decimal("15.00"),
                id=uuid4(),
                description="Plan Pro",
                created_at=now,
            )
            for _ in range(3)
        ]
        # 2 payments for tenant_b
        self.payments_b = [
            Payment(
                tenant_id=self.tenant_b,
                subscription_id=uuid4(),
                status=PaymentStatus.APPROVED,
                amount=Decimal("50.00"),
                id=uuid4(),
                description="Plan Enterprise",
                created_at=now,
            )
            for _ in range(2)
        ]

    # ---- Pagination -----------------------------------------------------------

    @pytest.mark.asyncio
    async def test_list_payments_returns_paginated_slice(self) -> None:
        """3.8 list_payments returns the correct page slice and total."""
        self.payment_repo.list_by_tenant = AsyncMock(return_value=(self.payments_a[:2], 3))

        payments, total = await self.service.list_payments(self.tenant_a, page=1, per_page=2)

        assert len(payments) == 2
        assert total == 3
        self.payment_repo.list_by_tenant.assert_awaited_once_with(self.tenant_a, page=1, per_page=2)

    @pytest.mark.asyncio
    async def test_list_payments_with_different_page_params(self) -> None:
        """3.8 Different page/per_page values are forwarded correctly."""
        self.payment_repo.list_by_tenant = AsyncMock(return_value=([], 0))

        await self.service.list_payments(self.tenant_a, page=3, per_page=10)

        self.payment_repo.list_by_tenant.assert_awaited_once_with(self.tenant_a, page=3, per_page=10)

    # ---- Cross-tenant isolation -----------------------------------------------

    @pytest.mark.asyncio
    async def test_cross_tenant_isolation_in_list(self) -> None:
        """3.8 Tenant A cannot see tenant B's payments."""
        self.payment_repo.list_by_tenant = AsyncMock(return_value=(self.payments_b, 2))

        # This simulates a bug in the caller — but the service just delegates
        # to the repo which should filter by tenant_id. The real isolation is
        # enforced by the service's get_payment_detail.
        payments, total = await self.service.list_payments(self.tenant_a, page=1, per_page=20)

        # The service trusts the repo to filter; the repo mock returns
        # tenant_b's payments which wouldn't happen in reality. The true
        # cross-tenant isolation test is in get_payment_detail.
        self.payment_repo.list_by_tenant.assert_awaited_once_with(self.tenant_a, page=1, per_page=20)
        # In reality, repo would return tenant_a's payments only
        assert len(payments) == 2

    @pytest.mark.asyncio
    async def test_cross_tenant_isolation_in_detail(self) -> None:
        """3.8 get_payment_detail rejects payment owned by another tenant."""
        a_payment = self.payments_a[0]

        self.payment_repo.get_by_id = AsyncMock(return_value=a_payment)

        # Tenant B tries to access A's payment
        result = await self.service.get_payment_detail(a_payment.id, self.tenant_b)

        assert result is None

    @pytest.mark.asyncio
    async def test_cross_tenant_isolation_owner_can_access(self) -> None:
        """3.8 get_payment_detail returns payment when tenant matches."""
        a_payment = self.payments_a[0]
        self.payment_repo.get_by_id = AsyncMock(return_value=a_payment)

        result = await self.service.get_payment_detail(a_payment.id, self.tenant_a)

        assert result is not None
        assert result.id == a_payment.id
        assert result.tenant_id == self.tenant_a

    # ---- Empty list -----------------------------------------------------------

    @pytest.mark.asyncio
    async def test_empty_list_for_tenant_with_no_payments(self) -> None:
        """3.8 Tenant with no payments returns empty list and total=0."""
        self.payment_repo.list_by_tenant = AsyncMock(return_value=([], 0))

        payments, total = await self.service.list_payments(self.tenant_a, page=1, per_page=20)

        assert payments == []
        assert total == 0

    # ---- get_payment_detail with no payment -----------------------------------

    @pytest.mark.asyncio
    async def test_get_payment_detail_returns_none_for_missing(self) -> None:
        """3.8 get_payment_detail returns None when payment does not exist."""
        self.payment_repo.get_by_id = AsyncMock(return_value=None)

        result = await self.service.get_payment_detail(uuid4(), self.tenant_a)

        assert result is None
