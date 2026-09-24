from uuid import UUID

from src.auth.application.ports.trial_provisioner import ITrialProvisioner
from src.billing.application.services._trial_management_service import (
    TrialManagementService,
)
from src.billing.domain.entities import PlanTypeEntity
from src.billing.domain.repositories import IPlanRepository, ISubscriptionRepository
from src.common.application.ports.uow import IUoW


class TrialProvisioner(ITrialProvisioner):
    """Billing adapter that provisions trials in the caller's transaction."""

    def __init__(self, trial_management_service: TrialManagementService) -> None:
        self.trial_management_service = trial_management_service

    async def provision_trial(self, tenant_id: UUID, uow: IUoW) -> None:
        plan_repository = uow.get_repository(IPlanRepository)
        subscription_repository = uow.get_repository(ISubscriptionRepository)
        await self.trial_management_service.start_trial(
            tenant_id,
            plan_repository,
            subscription_repository,
            PlanTypeEntity.FREE,
        )
