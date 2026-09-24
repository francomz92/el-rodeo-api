from typing import Annotated

from fastapi import Depends

from src.auth.application.ports.trial_provisioner import ITrialProvisioner
from src.auth.domain.services.change_password_service import ChangePasswordService
from src.auth.domain.services.login_user_service import LoginUserService
from src.auth.domain.services.register_user_service import RegisterUserService
from src.billing.application.services._trial_management_service import (
    TrialManagementService,
)
from src.billing.infrastructure.adapters.trial_provisioner import TrialProvisioner
from src.common.infrastructure.presentation.dependencies.security import GetSecurityService


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


def _get_register_user_service(security_service: GetSecurityService) -> RegisterUserService:
    """Factory for RegisterUserService (no dependencies)."""
    return RegisterUserService(security_service)


def _get_login_user_service(security_service: GetSecurityService) -> LoginUserService:
    """Factory for LoginUserService (no dependencies)."""
    return LoginUserService(security_service)


def _get_change_password_service(security_service: GetSecurityService) -> ChangePasswordService:
    """Factory for ChangePasswordService (no dependencies)."""
    return ChangePasswordService(security_service)
