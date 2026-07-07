"""MercadoPagoService — orchestrates MercadoPago Checkout Pro preferences.

Provides:
- create_checkout_preference: validates price > 0, creates MP preference, saves payment record
- get_payment_status: proxies to gateway
- refund_payment: proxies to gateway
"""

from decimal import Decimal
from uuid import UUID

from src.billing.domain.entities._payment import Payment
from src.billing.domain.entities._payment_status import PaymentStatus
from src.billing.domain.entities._plan_type import PlanType
from src.billing.domain.exceptions import PlanNotChangeableError
from src.billing.domain.repositories import (
    IPaymentGateway,
    IPaymentRepository,
    IPlanRepository,
    ISubscriptionRepository,
    ItemData,
    PaymentResult,
)
from src.common.application.ports.uow import IUoW
from src.common.infrastructure.core._config import settings


class MercadoPagoService:
    """Application service that orchestrates MercadoPago Checkout Pro interactions.

    Wraps the IPaymentGateway port with business logic (price validation,
    payment record creation) and exposes convenience methods for status
    lookup and refunds.
    """

    def __init__(
        self,
        gateway: IPaymentGateway,
        payment_repo: IPaymentRepository,
        subscription_repo: ISubscriptionRepository,
        plan_repo: IPlanRepository,
        uow_factory: IUoW,
    ) -> None:
        self._gateway = gateway
        self._payment_repo = payment_repo
        self._subscription_repo = subscription_repo
        self._plan_repo = plan_repo
        self._uow_factory = uow_factory

    async def create_checkout_preference(
        self,
        tenant_id: UUID,
        plan_type: PlanType,
    ) -> str:
        """Create an MP Checkout Pro preference for the given tenant and plan.

        Loads the plan, validates it is a paid plan (price > 0), builds the
        preference payload, delegates to the gateway, persists a PENDING
        Payment record, and returns the checkout ``init_point`` URL.

        Args:
            tenant_id: The tenant requesting the checkout.
            plan_type: The target plan type.

        Returns:
            The MercadoPago Checkout Pro ``init_point`` URL.

        Raises:
            PlanNotChangeableError: If the plan is FREE or has no price.
            ValueError: If no subscription exists for the tenant.
        """
        # Load plan from the injected PlanRepository (in-memory seed data)
        plan = await self._plan_repo.get_by_plan_type(plan_type)

        # GUARD: FREE plan / zero-price plans cannot be purchased
        if plan.price_monthly is None or plan.price_monthly.amount <= Decimal("0"):
            raise PlanNotChangeableError("FREE plan cannot be purchased")

        # Load subscription to obtain the subscription_id for the Payment record
        subscription = await self._subscription_repo.get_by_tenant(tenant_id)
        if subscription is None:
            raise ValueError(f"No subscription found for tenant {tenant_id}")

        # Build the checkout preference payload
        item = ItemData(
            title=f"Plan {plan.name} - El Rodeo",
            quantity=1,
            unit_price=plan.price_monthly.amount,
            currency_id="ARS",
        )

        external_reference = f"{tenant_id}:{plan_type.value}"

        back_urls = {
            "success": settings.MP_WEBHOOK_URL,
            "failure": settings.MP_WEBHOOK_URL,
            "pending": settings.MP_WEBHOOK_URL,
        }

        result = await self._gateway.create_preference(
            items=[item],
            back_urls=back_urls,
            notification_url=settings.MP_WEBHOOK_URL,
            external_reference=external_reference,
        )

        # Persist a PENDING payment record
        payment = Payment(
            tenant_id=tenant_id,
            subscription_id=subscription.id,
            status=PaymentStatus.PENDING,
            amount=plan.price_monthly.amount,
            mp_preference_id=result.id,
            description=f"Plan {plan.name} - El Rodeo",
        )
        await self._payment_repo.create(payment)

        return result.init_point

    async def get_payment_status(self, mp_payment_id: str) -> PaymentResult:
        """Retrieve the current status of a MercadoPago payment.

        Delegates directly to the gateway.
        """
        return await self._gateway.get_payment(mp_payment_id)

    async def refund_payment(
        self,
        mp_payment_id: str,
        amount: Decimal | None = None,
    ) -> bool:
        """Refund a MercadoPago payment, fully or partially.

        Delegates directly to the gateway.
        """
        return await self._gateway.refund(mp_payment_id, amount)
