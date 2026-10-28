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
    async def list_by_tenant(self, tenant_id: UUID, page: int = 1, per_page: int = 20) -> tuple[list[PaymentEntity], int]:
        """Paginated list of payments for a tenant. Returns (items, total)."""
        raise NotImplementedError
