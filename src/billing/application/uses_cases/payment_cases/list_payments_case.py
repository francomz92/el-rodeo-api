"""ListPaymentsCase — paginated payment history with tenant isolation."""

from uuid import UUID

from src.billing.domain.entities.payments import PaymentEntity
from src.billing.domain.repositories import IPaymentRepository
from src.common.application.ports.uow import IUoW


class ListPaymentsCase:
    """Use case for listing a tenant's payment history.

    All queries are scoped to the requesting tenant to enforce cross-tenant
    isolation.
    """

    def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def execute(
        self,
        tenant_id: UUID,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[PaymentEntity], int]:
        """Return a paginated list of payments for a tenant.

        Args:
            tenant_id: The tenant whose payments to list.
            page: Page number (1-indexed).
            per_page: Items per page (default 20).

        Returns:
            A tuple of ``(payments, total_count)``.
        """
        async with self.uow as uow:
            payment_repo = uow.get_repository(IPaymentRepository)
            return await payment_repo.list_by_tenant(
                tenant_id,
                page=page,
                per_page=per_page,
            )
