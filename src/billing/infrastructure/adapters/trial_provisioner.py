from uuid import UUID

from src.auth.application.ports.trial_provisioner import ITrialProvisioner
from src.billing.application.uses_cases.trial_cases.start_trial_case import (
    StartTrialCase,
)
from src.billing.domain.entities import PlanTypeEntity
from src.common.application.ports.uow import IUoW


class TrialProvisioner(ITrialProvisioner):
    """Billing adapter that provisions trials in the caller's transaction.

    Ownership contract: the caller's ``uow`` always wins. If the
    DI-provided case was built on a different uow, it is rebuilt on the
    caller's uow (same service), so the trial joins the tenant-creation
    transaction instead of opening its own.
    """

    def __init__(self, start_trial_case: StartTrialCase) -> None:
        self.start_trial_case = start_trial_case

    async def provision_trial(self, tenant_id: UUID, uow: IUoW) -> None:
        case = self.start_trial_case
        if case.uow is not uow:
            # Honour the caller's transaction: the case must run on the uow
            # that owns the surrounding flow (tenant creation).
            case = StartTrialCase(uow=uow, service=case.service)
        # I6 (L8): new-tenant trials grant the PRO plan. Entitlements are
        # plan-read live by quota/feature checks; nothing is copied here.
        await case.execute(
            tenant_id,
            plan_type=PlanTypeEntity.PRO,
        )
