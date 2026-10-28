"""CreateCheckoutCase — orchestrates MercadoPago Checkout Pro preferences.

Provides:
- execute: validates price > 0, creates MP preference, saves payment record,
  returns the checkout ``init_point`` URL.
"""

from decimal import Decimal
from uuid import UUID

from src.billing.domain.constants.payments import PaymentStatus
from src.billing.domain.constants.plans import PlanTypeEntity
from src.billing.domain.entities.payments import PaymentEntity
from src.billing.domain.exceptions import PlanNotChangeableError
from src.billing.domain.repositories import (
    BackUrlsData,
    IPaymentGateway,
    IPaymentRepository,
    IPlanRepository,
    ISubscriptionRepository,
    ItemData,
)
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotFoundError


class CreateCheckoutCase:
    """Use case that creates a MercadoPago Checkout Pro preference.

    Wraps the IPaymentGateway port with business logic (price validation,
    payment record creation) and returns the checkout URL.
    """

    def __init__(
        self,
        uow: IUoW,
        gateway: IPaymentGateway,
        webhook_url: str,
    ) -> None:
        self.uow = uow
        self.gateway = gateway
        self.webhook_url = webhook_url

    async def execute(
        self,
        tenant_id: UUID,
        plan_type: PlanTypeEntity,
    ) -> str:
        """Create an MP Checkout Pro preference for the given tenant and plan.

        Loads the plan, validates it is a paid plan (price > 0), builds the
        preference payload, delegates to the gateway, persists a PENDING
        PaymentEntity record, and returns the checkout ``init_point`` URL.

        Args:
            tenant_id: The tenant requesting the checkout.
            plan_type: The target plan type.

        Returns:
            The MercadoPago Checkout Pro ``init_point`` URL.

        Raises:
            PlanNotChangeableError: If the plan is FREE, unpriced, or not found.
            NotFoundError: If no subscription exists for the tenant.
        """
        async with self.uow as uow:
            plan_repo = uow.get_repository(IPlanRepository)
            subscription_repo = uow.get_repository(ISubscriptionRepository)
            payment_repo = uow.get_repository(IPaymentRepository)

            # Load plan from the injected PlanRepository (in-memory seed data)
            plan = await plan_repo.get_by_plan_type(plan_type)
            if plan is None:
                raise PlanNotChangeableError(f"No existe el plan: {plan_type.value}")

            # GUARD: FREE plan / zero-price plans cannot be purchased
            if plan.price_monthly is None or plan.price_monthly.amount <= Decimal("0"):
                raise PlanNotChangeableError("El plan FREE no se puede comprar")

            # Load subscription to obtain the subscription_id for the PaymentEntity record
            subscription = await subscription_repo.get_current_by_tenant(tenant_id)
            if subscription is None:
                raise NotFoundError(f"No existe una suscripción para el tenant {tenant_id}")

            # Build the checkout preference payload
            item = ItemData(
                title=f"Plan {plan.name} - El Rodeo",
                quantity=1,
                unit_price=plan.price_monthly.amount,
                currency_id="ARS",
            )

            external_reference = f"{tenant_id}:{plan_type.value}"

            back_urls = BackUrlsData(
                success=self.webhook_url,
                failure=self.webhook_url,
                pending=self.webhook_url,
            )

            result = await self.gateway.create_preference(
                items=[item],
                back_urls=back_urls,
                notification_url=self.webhook_url,
                external_reference=external_reference,
            )

            # Persist a PENDING payment record
            payment = PaymentEntity(
                tenant_id=tenant_id,
                subscription_id=subscription.id,
                status=PaymentStatus.PENDING,
                amount=plan.price_monthly.amount,
                mp_preference_id=result.id,
                description=f"Plan {plan.name} - El Rodeo",
            )
            await payment_repo.create(payment)
            await uow.commit()

            return result.init_point
