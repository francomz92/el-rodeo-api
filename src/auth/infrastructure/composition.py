from typing import Annotated

from fastapi import Depends

from src.auth.application.ports.trial_provisioner import ITrialProvisioner
from src.auth.application.services.authentication_service import AuthService
from src.auth.application.uses_cases.change_password_case import ChangePasswordCase
from src.auth.application.uses_cases.create_tenant_case import CreateTenantCase
from src.auth.application.uses_cases.login_user_case import LoginUserCase
from src.auth.application.uses_cases.logout_user_case import LogoutUserCase
from src.auth.application.uses_cases.refresh_token_case import RefreshTokenCase
from src.auth.domain.services.change_password_service import ChangePasswordService
from src.auth.domain.services.login_user_service import LoginUserService
from src.auth.domain.services.register_user_service import RegisterUserService
from src.billing.application.services._trial_management_service import (
    TrialManagementService,
)
from src.billing.infrastructure.adapters.trial_provisioner import TrialProvisioner
from src.common.infrastructure.core import settings
from src.common.infrastructure.events.handlers.email_notification import EmailNotificationHandler
from src.common.infrastructure.presentation.dependencies.event_bus import GetEventBus
from src.common.infrastructure.presentation.dependencies.notifier import GetNotifierClient
from src.common.infrastructure.presentation.dependencies.redis import GetTokenBlacklistService
from src.common.infrastructure.presentation.dependencies.security import GetSecurityService
from src.common.infrastructure.presentation.dependencies.token import GetTokenService
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_trial_management_service() -> TrialManagementService:
    """Build the trial management service used by the billing adapter."""
    return TrialManagementService(trial_days=settings.TRIAL_DAYS)


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


def _get_create_tenant_case(
    uow: GetUnitOfWork,
    security_service: GetSecurityService,
    register_service: Annotated[RegisterUserService, Depends(_get_register_user_service)],
    bus: GetEventBus,
    notifier: GetNotifierClient,
    token_service: GetTokenService,
    trial_provisioner: GetTrialProvisioner,
) -> CreateTenantCase:
    bus.register("tenant_registered", EmailNotificationHandler(notifier))
    return CreateTenantCase(
        uow=uow,
        security_service=security_service,
        register_service=register_service,
        event_bus=bus,
        token_service=token_service,
        trial_provisioner=trial_provisioner,
    )


def _get_login_user_case(
    uow: GetUnitOfWork,
    security_service: GetSecurityService,
    token_service: GetTokenService,
    login_service: Annotated[LoginUserService, Depends(_get_login_user_service)],
) -> LoginUserCase:
    return LoginUserCase(
        uow=uow,
        security_service=security_service,
        token_service=token_service,
        login_service=login_service,
        refresh_token_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )


def _get_auth_service(
    token_service: GetTokenService,
    blacklist_service: GetTokenBlacklistService,
) -> AuthService:
    return AuthService(
        token_service=token_service,
        blacklist_service=blacklist_service,
    )


def _get_logout_user_case(
    token_service: GetTokenService,
    blacklist_service: GetTokenBlacklistService,
    uow: GetUnitOfWork,
) -> LogoutUserCase:
    return LogoutUserCase(
        token_service=token_service,
        blacklist_service=blacklist_service,
        uow=uow,
    )


def _get_refresh_token_case(
    token_service: GetTokenService,
    uow: GetUnitOfWork,
) -> RefreshTokenCase:
    return RefreshTokenCase(
        token_service=token_service,
        uow=uow,
    )


def _get_change_password_case(
    uow: GetUnitOfWork,
    change_password_service: Annotated[ChangePasswordService, Depends(_get_change_password_service)],
) -> ChangePasswordCase:
    return ChangePasswordCase(uow=uow, change_password_service=change_password_service)
