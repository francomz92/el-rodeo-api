"""ListPaymentsCase — cursor-paginated payment history with tenant isolation."""

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
        limit: int,
        offset: int = 0,
        order_by: str = "id",
        cursor: str | None = None,
    ) -> tuple[list[PaymentEntity], int, bool]:
        """Return a keyset page of payments for a tenant.

        Args:
            tenant_id: The tenant whose payments to list.
            limit: Maximum rows to return (the repo probes limit + 1).
            offset: Skip rows before the page (ignored when cursor is set).
            order_by: Sort column; mapped to a Payment column (id fallback).
            cursor: Opaque continuation token from a previous page.

        Returns:
            A tuple of ``(payments, total_count, has_next)``.
        """
        async with self.uow as uow:
            payment_repo = uow.get_repository(IPaymentRepository)
            return await payment_repo.list_by_tenant(
                tenant_id,
                limit=limit,
                offset=offset,
                order_by=order_by,
                cursor=cursor,
            )
