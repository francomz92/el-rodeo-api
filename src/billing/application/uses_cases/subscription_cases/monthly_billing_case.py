"""MonthlyBillingCase — creates MP checkout preferences for due subscriptions.

System-worker batch: iterates ALL tenants, so it sets ``bypass_filter`` on its
unit of work — the standard cross-tenant signal for any ``TenantAwareRepository``
the UoW builds. Note that the billing repositories scope ``tenant_id``
explicitly per query and do not inherit ``TenantAwareRepository``, so the flag
does not change their queries (F2-4 map #8). For every ACTIVE subscription whose
``current_period_end`` is within the next 7 days, a PENDING payment record
and a MercadoPago Checkout Pro preference are created for the same plan.
Gateway-managed subscriptions are skipped (they auto-charge). Errors are
logged per subscription without crashing the batch.
"""

from __future__ import annotations

from src.billing.domain.constants.payments import PaymentStatus
from src.billing.domain.entities.payments import PaymentEntity
from src.billing.domain.repositories import (
    BackUrlsData,
    IPaymentGateway,
    IPaymentRepository,
    IPlanRepository,
    ISubscriptionRepository,
    ItemData,
)
from src.common.application.ports.uow import IUoWFactory
from src.common.utils import log


class MonthlyBillingCase:
    """Use case that bills ACTIVE subscriptions near their period end."""

    def __init__(
        self,
        uow_factory: IUoWFactory,
        gateway: IPaymentGateway,
        frontend_url: str,
        webhook_url: str,
    ) -> None:
        self.uow_factory = uow_factory
        self.gateway = gateway
        self.frontend_url = frontend_url
        self.webhook_url = webhook_url

    async def execute(self) -> dict:
        """Create checkout preferences for ACTIVE subscriptions near period end.

        Returns:
            A summary dict with ``processed``, ``succeeded``, and ``failed``
            counts for monitoring.
        """
        uow = self.uow_factory()
        # System worker iterating every tenant. No-op for the billing repos
        # (they scope tenant_id per query — F2-4 map #8), but it is the
        # standard signal for any TenantAwareRepository this UoW builds.
        uow.bypass_filter = True

        async with uow:
            sub_repo: ISubscriptionRepository = uow.get_repository(ISubscriptionRepository)
            plan_repo: IPlanRepository = uow.get_repository(IPlanRepository)
            payment_repo: IPaymentRepository = uow.get_repository(IPaymentRepository)

            subs = await sub_repo.list_active_near_period_end(7)

            if not subs:
                log.info("monthly_billing — no subscriptions near period end")
                return {"processed": 0, "succeeded": 0, "failed": 0}

            # Filter out gateway-managed subscriptions — they auto-charge via gateway
            legacy_subs = [s for s in subs if s.gateway_subscription_id is None]
            skipped_mp = len(subs) - len(legacy_subs)
            if skipped_mp:
                log.info(
                    "monthly_billing — skipping {} MP-managed subscriptions",
                    skipped_mp,
                )

            if not legacy_subs:
                log.info("monthly_billing — no legacy subscriptions to process")
                return {"processed": len(subs), "succeeded": 0, "failed": 0}

            succeeded = 0
            failed = 0

            for idx, sub in enumerate(legacy_subs):
                try:
                    plan = await plan_repo.get_by_id(sub.plan_id)
                    if plan is None:
                        log.warning(
                            "monthly_billing — plan not found",
                            sub_id=str(sub.id),
                            plan_id=str(sub.plan_id),
                        )
                        failed += 1
                        continue

                    # FREE / zero-price plans need no billing
                    if plan.price_monthly is None or plan.price_monthly.amount <= 0:
                        log.info(
                            "monthly_billing — skipping free plan",
                            sub_id=str(sub.id),
                            plan_type=plan.plan_type.value,
                        )
                        succeeded += 1
                        continue

                    # Build checkout payload
                    item = ItemData(
                        title=f"Plan {plan.name} - El Rodeo",
                        quantity=1,
                        unit_price=plan.price_monthly.amount,
                        currency_id="ARS",
                    )

                    external_ref = f"{sub.tenant_id}:{plan.plan_type.value}"

                    result = await self.gateway.create_preference(
                        items=[item],
                        back_urls=BackUrlsData(
                            success=f"{self.frontend_url}/payment/success",
                            failure=f"{self.frontend_url}/payment/failure",
                            pending=f"{self.frontend_url}/payment/pending",
                        ),
                        notification_url=self.webhook_url,
                        external_reference=external_ref,
                    )

                    # Persist PENDING payment record
                    payment = PaymentEntity(
                        tenant_id=sub.tenant_id,
                        subscription_id=sub.id,
                        status=PaymentStatus.PENDING,
                        amount=plan.price_monthly.amount,
                        mp_preference_id=result.id,
                        description=f"Plan {plan.name} - El Rodeo",
                    )
                    await payment_repo.create(payment)

                    await uow.commit()

                    log.info(
                        "monthly_billing — created preference",
                        tenant_id=str(sub.tenant_id),
                        preference_id=result.id,
                        idx=idx,
                    )
                    succeeded += 1

                except Exception:
                    await uow.rollback()
                    log.exception(
                        "monthly_billing — failed for subscription",
                        tenant_id=str(sub.tenant_id),
                        sub_id=str(sub.id),
                    )
                    failed += 1

            log.info(
                "monthly_billing completed",
                processed=len(subs),
                succeeded=succeeded,
                failed=failed,
            )
            return {"processed": len(subs), "succeeded": succeeded, "failed": failed}
