"""StartTrialCase — creates a configured-duration trial for a new tenant."""

from uuid import UUID

from src.billing.domain.constants.plans import PlanTypeEntity
from src.billing.domain.entities.subscriptions import SubscriptionEntity
from src.billing.domain.repositories import IPlanRepository, ISubscriptionRepository
from src.billing.domain.services.subscription_services.trial_service import TrialService
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import DuplicatedError


class StartTrialCase:
    """Use case that creates a trial subscription for a new tenant.

    Runs inside the caller's transaction: it deliberately does NOT open its
    own ``async with`` boundary nor commit — the caller (tenant creation,
    via ``TrialProvisioner``) owns the transaction and the commit.
    """

    def __init__(
        self,
        uow: IUoW,
        service: TrialService,
    ) -> None:
        self.uow = uow
        self.service = service

    async def execute(
        self,
        tenant_id: UUID,
        plan_type: PlanTypeEntity = PlanTypeEntity.PRO,
    ) -> SubscriptionEntity:
        """Create a trial subscription for the given tenant.

        Fetches the plan by type, creates a TRIAL status subscription
        with trial_end = now + the configured trial duration, and persists it.
        """
        plan_repository = self.uow.get_repository(IPlanRepository)
        subscription_repository = self.uow.get_repository(ISubscriptionRepository)

        # A.15 (L15): a tenant holds exactly one subscription — enforce it
        # at the write path too (the DB adds the UNIQUE constraint).
        existing = await subscription_repository.get_current_by_tenant(tenant_id)
        if existing is not None:
            raise DuplicatedError(f"El tenant {tenant_id} ya tiene una suscripción ({existing.status.value})")

        plan = await plan_repository.get_by_plan_type(plan_type)
        if plan is None:
            raise ValueError(f"No existe el plan: {plan_type.value}")

        subscription = self.service.build_trial_subscription(
            tenant_id=tenant_id,
            plan=plan,
        )

        return await subscription_repository.create(subscription)
