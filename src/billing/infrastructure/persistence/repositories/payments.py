"""SQLAlchemy implementation of IPaymentRepository."""

from uuid import UUID

from sqlalchemy import RowMapping, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.billing.domain.entities.payments import PaymentEntity
from src.billing.domain.repositories import IPaymentRepository
from src.billing.infrastructure.persistence.models import Payment as PaymentModel
from src.billing.infrastructure.persistence.repositories.mappers import build_payment
from src.common.application.pagination.cursor import cursor_uuid, decode_cursor

_LISTING_COLUMNS = (
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

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        limit: int,
        offset: int = 0,
        order_by: str = "id",
        cursor: str | None = None,
    ) -> tuple[list[PaymentEntity], int, bool]:
        """Tenant-scoped keyset page of payments. Returns (items, total, has_next)."""
        # ── Explicit order column resolution ────────────────────────
        # The shared query catalog also allows "name", which the payment
        # table has not; map only columns that exist on this model and
        # fall back to id so sort and keyset stay coherent (the raw
        # order_by string never reaches .order_by()).
        order_column = {
            "id": PaymentModel.id,
            "created_at": PaymentModel.created_at,
            "updated_at": PaymentModel.updated_at,
        }.get(order_by, PaymentModel.id)

        # ── Count total (filter-wide, not cursor-sliced) ────────────
        count_stmt = select(func.count()).select_from(PaymentModel).where(PaymentModel.tenant_id == tenant_id)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # ── Data query ──────────────────────────────────────────────
        if cursor is not None:
            cursor_data = decode_cursor(cursor)
            cursor_id = cursor_uuid(cursor_data)
            # The token carries id + sort_value, but only the id
            # comparison applies here (same limitation as animals).
            stmt = (
                select(
                    *_LISTING_COLUMNS,
                )
                .where(PaymentModel.tenant_id == tenant_id, PaymentModel.id > cursor_id)
                .order_by(order_column)
                .limit(limit + 1)  # fetch one extra to detect next page
            )
        else:
            stmt = (
                select(
                    *_LISTING_COLUMNS,
                )
                .where(PaymentModel.tenant_id == tenant_id)
                .order_by(order_column)
                .offset(offset)
                .limit(limit + 1)  # fetch one extra to detect next page
            )
        result = await self.db.execute(stmt)
        rows = result.mappings().all()

        # Both modes fetch one extra row (limit+1) so has_next is always
        # observable — the first page must hand the FE the next_cursor.
        has_next = len(rows) > limit
        if has_next:
            rows = rows[:limit]

        items = [self._build_entity(row) for row in rows]
        return items, total, has_next

    @staticmethod
    def _build_entity(row: RowMapping) -> PaymentEntity:
        """Build a PaymentEntity domain entity from a row mapping."""
        return build_payment(row)
