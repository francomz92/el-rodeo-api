"""SQLAlchemy implementation of IPaymentRepository."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import RowMapping, func, insert, select

from src.billing.domain.entities._payment import Payment, PaymentMethod
from src.billing.domain.entities._payment_status import PaymentStatus
from src.billing.domain.repositories import IPaymentRepository
from src.billing.infrastructure.persistence.models import Payment as PaymentModel
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)


class PaymentRepository(IPaymentRepository, TenantAwareRepository):
    """SQLAlchemy async implementation of IPaymentRepository."""

    @property
    def _model(self) -> type:
        return PaymentModel

    async def create(self, payment: Payment) -> Payment:
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

    async def get_by_id(self, id: UUID) -> Payment | None:
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

    async def get_by_tenant(self, tenant_id: UUID) -> list[Payment]:
        """Retrieve all payments for a tenant."""
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
        ).where(PaymentModel.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return [self._build_entity(row) for row in result.mappings().all()]

    async def get_by_mp_payment_id(self, mp_payment_id: str) -> Payment | None:
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

    async def list_by_tenant(self, tenant_id: UUID, page: int = 1, per_page: int = 20) -> tuple[list[Payment], int]:
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
    def _build_entity(row: RowMapping) -> Payment:
        """Build a Payment domain entity from a row mapping."""
        raw_method = row.get("payment_method")
        payment_method: PaymentMethod | None = None
        if raw_method and "|" in raw_method:
            parts = raw_method.split("|", 1)
            payment_method = PaymentMethod(
                card_brand=parts[0] or None,
                payment_type_id=parts[1] or None,
            )

        return Payment(
            id=row["id"],
            tenant_id=row["tenant_id"],
            subscription_id=row["subscription_id"],
            mp_payment_id=row.get("mp_payment_id"),
            mp_preference_id=row.get("mp_preference_id"),
            status=PaymentStatus(row["status"]),
            amount=Decimal(str(row["amount"])),
            currency=row.get("currency", "ARS"),
            description=row.get("description"),
            payment_method=payment_method,
            installments=row.get("installments"),
            paid_at=row.get("paid_at"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
