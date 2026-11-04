from abc import abstractmethod
from uuid import UUID

from src.billing.domain.entities.payments import PaymentEntity
from src.common.domain.repository import IRepository


class IPaymentRepository(IRepository):
    @abstractmethod
    async def create(self, payment: PaymentEntity) -> PaymentEntity:
        """Persist a new payment."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID) -> PaymentEntity | None:
        """Retrieve a payment by its UUID, or None."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_mp_payment_id(self, mp_payment_id: str) -> PaymentEntity | None:
        """Retrieve a payment by its MercadoPago payment ID, or None."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        limit: int,
        offset: int = 0,
        order_by: str = "id",
        cursor: str | None = None,
    ) -> tuple[list[PaymentEntity], int, bool]:
        """List a tenant's payments; returns ``(items, total_count, has_next)``.

        With ``cursor``, the page continues after that opaque token (keyset
        on the payments id); ``total`` always counts every row matching the
        tenant scope, independent of the cursor slice.
        """
        raise NotImplementedError
