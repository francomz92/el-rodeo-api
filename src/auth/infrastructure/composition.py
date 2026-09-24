from typing import Annotated

from fastapi import Depends

from src.auth.application.ports.trial_provisioner import ITrialProvisioner
from src.billing.application.services._trial_management_service import (
    TrialManagementService,
)
from src.billing.infrastructure.adapters.trial_provisioner import TrialProvisioner


def _get_trial_management_service() -> TrialManagementService:
    """Build the trial management service used by the billing adapter."""
    return TrialManagementService()


GetTrialManagementService = Annotated[
    TrialManagementService,
    Depends(_get_trial_management_service),
]


def _get_trial_provisioner(
    trial_service: GetTrialManagementService,
) -> ITrialProvisioner:
    return TrialProvisioner(trial_service)


GetTrialProvisioner = Annotated[
    ITrialProvisioner,
    Depends(_get_trial_provisioner),
]
