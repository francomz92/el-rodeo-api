"""SQLAlchemy implementation of IPaymentRepository."""

from uuid import UUID

from sqlalchemy import RowMapping, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.billing.domain.entities.payments import PaymentEntity
from src.billing.domain.repositories import IPaymentRepository
from src.billing.infrastructure.persistence.models import Payment as PaymentModel
from src.billing.infrastructure.persistence.repositories.mappers import build_payment


class PaymentRepository(IPaymentRepository):
    """SQLAlchemy async implementation of IPaymentRepository.

    Tenant scoping is explicit per query: the tenant-scoped statements carry
    ``tenant_id`` in their WHERE clause. This repository deliberately does NOT
    inherit ``TenantAwareRepository`` — it never called ``_filter_tenant``, so
    the base class and the ``bypass_filter`` flag it carries were inert here
    (F2-4 map #8, odd/tasks/billing-refactor.md).
    """

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def create(self, payment: PaymentEntity) -> PaymentEntity:
        """Persist a new payment and return it."""
        stmt = (
            insert(PaymentModel)
            .values(
                {
                    PaymentModel.id: payment.id,
                    PaymentModel.tenant_id: payment.tenant_id,
                    PaymentModel.subscription_id: payment.subscription_id,
                    PaymentModel.mp_payment_id: payment.mp_payment_id,
                    PaymentModel.mp_preference_id: payment.mp_preference_id,
                    PaymentModel.status: payment.status.value,
                    PaymentModel.amount: payment.amount,
                    PaymentModel.currency: payment.currency,
                    PaymentModel.description: payment.description,
                    PaymentModel.payment_method: (
                        f"{payment.payment_method.card_brand}|{payment.payment_method.payment_type_id}" if payment.payment_method else None
                    ),
                    PaymentModel.installments: payment.installments,
                    PaymentModel.paid_at: payment.paid_at,
                }
            )
            .returning(PaymentModel.id)
        )
        result = await self.db.execute(stmt)
        payment_id = result.scalar_one()
        return await self.get_by_id(payment_id)  # type: ignore

    async def get_by_id(self, id: UUID) -> PaymentEntity | None:
        """Retrieve a payment by its UUID, or None."""
        stmt = select(
            PaymentModel.id,
            PaymentModel.tenant_id,
            PaymentModel.subscription_id,
            PaymentModel.mp_payment_id,
            PaymentModel.mp_preference_id,
            PaymentModel.status,
            PaymentModel.amount,
            PaymentModel.currency,
            PaymentModel.description,
            PaymentModel.payment_method,
            PaymentModel.installments,
            PaymentModel.paid_at,
            PaymentModel.created_at,
            PaymentModel.updated_at,
        ).where(PaymentModel.id == id)
        result = await self.db.execute(stmt)
        row = result.mappings().one_or_none()
        return self._build_entity(row) if row else None

    async def get_by_mp_payment_id(self, mp_payment_id: str) -> PaymentEntity | None:
        """Retrieve a payment by its MercadoPago payment ID, or None."""
        stmt = select(
            PaymentModel.id,
            PaymentModel.tenant_id,
            PaymentModel.subscription_id,
            PaymentModel.mp_payment_id,
            PaymentModel.mp_preference_id,
            PaymentModel.status,
            PaymentModel.amount,
            PaymentModel.currency,
            PaymentModel.description,
            PaymentModel.payment_method,
            PaymentModel.installments,
            PaymentModel.paid_at,
            PaymentModel.created_at,
            PaymentModel.updated_at,
        ).where(PaymentModel.mp_payment_id == mp_payment_id)
        result = await self.db.execute(stmt)
        row = result.mappings().one_or_none()
        return self._build_entity(row) if row else None

    async def list_by_tenant(self, tenant_id: UUID, page: int = 1, per_page: int = 20) -> tuple[list[PaymentEntity], int]:
        """Paginated list of payments for a tenant. Returns (items, total)."""
        # Count total
        count_stmt = select(func.count()).select_from(PaymentModel).where(PaymentModel.tenant_id == tenant_id)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Fetch page
        offset = (page - 1) * per_page
        stmt = (
            select(
                PaymentModel.id,
                PaymentModel.tenant_id,
                PaymentModel.subscription_id,
                PaymentModel.mp_payment_id,
                PaymentModel.mp_preference_id,
                PaymentModel.status,
                PaymentModel.amount,
                PaymentModel.currency,
                PaymentModel.description,
                PaymentModel.payment_method,
                PaymentModel.installments,
                PaymentModel.paid_at,
                PaymentModel.created_at,
                PaymentModel.updated_at,
            )
            .where(PaymentModel.tenant_id == tenant_id)
            .order_by(PaymentModel.created_at)
            .offset(offset)
            .limit(per_page)
        )
        result = await self.db.execute(stmt)
        items = [self._build_entity(row) for row in result.mappings().all()]
        return items, total

    @staticmethod
    def _build_entity(row: RowMapping) -> PaymentEntity:
        """Build a PaymentEntity domain entity from a row mapping."""
        return build_payment(row)
