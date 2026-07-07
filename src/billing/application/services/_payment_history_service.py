"""PaymentHistoryService — paginated payment history with tenant isolation.

Provides:
- list_payments: paginated list of payments for a tenant
- get_payment_detail: single payment with cross-tenant guard
"""

from uuid import UUID

from src.billing.domain.entities._payment import Payment
from src.billing.domain.repositories import IPaymentRepository


class PaymentHistoryService:
    """Application service for querying payment history.

    All queries are scoped to the requesting tenant to enforce cross-tenant
    isolation.
    """

    def __init__(self, payment_repo: IPaymentRepository) -> None:
        self._payment_repo = payment_repo

    async def list_payments(
        self,
        tenant_id: UUID,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Payment], int]:
        """Return a paginated list of payments for a tenant.

        Args:
            tenant_id: The tenant whose payments to list.
            page: Page number (1-indexed).
            per_page: Items per page (default 20).

        Returns:
            A tuple of ``(payments, total_count)``.
        """
        return await self._payment_repo.list_by_tenant(
            tenant_id,
            page=page,
            per_page=per_page,
        )

    async def get_payment_detail(
        self,
        payment_id: UUID,
        tenant_id: UUID,
    ) -> Payment | None:
        """Return a single payment after verifying tenant ownership.

        Args:
            payment_id: The payment UUID.
            tenant_id: The requesting tenant (used for isolation check).

        Returns:
            The Payment if found and owned by the tenant, otherwise None.
        """
        payment = await self._payment_repo.get_by_id(payment_id)
        if payment is None:
            return None
        if payment.tenant_id != tenant_id:
            return None
        return payment
