from abc import abstractmethod
from uuid import UUID

from src.billing.domain.entities._payment import Payment
from src.common.domain.repository import IRepository


class IPaymentRepository(IRepository):
    @abstractmethod
    async def create(self, payment: Payment) -> Payment:
        """Persist a new payment."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Payment | None:
        """Retrieve a payment by its UUID, or None."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_tenant(self, tenant_id: UUID) -> list[Payment]:
        """Retrieve all payments for a tenant."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_mp_payment_id(self, mp_payment_id: str) -> Payment | None:
        """Retrieve a payment by its MercadoPago payment ID, or None."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_tenant(self, tenant_id: UUID, page: int = 1, per_page: int = 20) -> tuple[list[Payment], int]:
        """Paginated list of payments for a tenant. Returns (items, total)."""
        raise NotImplementedError
