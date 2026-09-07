from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.application.services.authentication_service import AuthService
from src.auth.application.services.notifications.wellcome_email_service import (
    WellcomeEmailService,
)
from src.auth.application.uses_cases.change_password_case import ChangePasswordCase
from src.auth.application.uses_cases.create_tenant_case import CreateTenantCase
from src.auth.application.uses_cases.login_user_case import LoginUserCase
from src.auth.application.uses_cases.logout_user_case import LogoutUserCase
from src.auth.application.uses_cases.refresh_token_case import RefreshTokenCase
from src.auth.domain.entities import TenantEntity, UserEntity, UserRole
from src.auth.domain.repositories.tenant_repository_port import ITenantRepository
from src.auth.domain.services.change_password_service import ChangePasswordService
from src.auth.domain.services.login_user_service import LoginUserService
from src.auth.domain.services.register_user_service import RegisterUserService
from src.billing.application.services._trial_management_service import (
    TrialManagementService,
)
from src.common.domain.exceptions import NotPermissionError, UnauthorizedError
from src.common.infrastructure.presentation.dependencies.notifier import GetNotifierClient
from src.common.infrastructure.presentation.dependencies.redis import GetTokenBlacklistService
from src.common.infrastructure.presentation.dependencies.security import GetSecurityService
from src.common.infrastructure.presentation.dependencies.token import GetTokenService
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork

oauth2_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="Bearer token for authentication.",
    auto_error=False,
)


def _get_oauth_token(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(oauth2_scheme)],
) -> HTTPAuthorizationCredentials | None:
    """Extract the OAuth2 token from the Authorization header.
    Returns:
        HTTPAuthorizationCredentials: The extracted credentials.
    """
    if request.headers.get("x-requested-with") != "XMLHttpRequest":
        return credentials

    access_token = request.cookies.get("access_token")
    if access_token is None:
        return None

    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=access_token,
    )


async def _get_refresh_token(
    request: Request,
) -> str | None:
    """Extract the refresh token from the request cookies."""
    if request.headers.get("x-requested-with") != "XMLHttpRequest":
        data = await request.json()
        return data.get("refresh_token", "")
    return request.cookies.get("refresh_token", "")


def get_wellcome_notifier_service(
    notifier_client: GetNotifierClient,
) -> WellcomeEmailService:
    return WellcomeEmailService(notifier_client)


def _get_register_user_service() -> RegisterUserService:
    """Factory for RegisterUserService (no dependencies)."""
    return RegisterUserService()


def _get_login_user_service() -> LoginUserService:
    """Factory for LoginUserService (no dependencies)."""
    return LoginUserService()


def _get_change_password_service() -> ChangePasswordService:
    """Factory for ChangePasswordService (no dependencies)."""
    return ChangePasswordService()


def _get_trial_management_service(uow: GetUnitOfWork) -> TrialManagementService:
    """Build a request-scoped TrialManagementService sharing the UoW session."""
    return TrialManagementService()


GetTrialManagementService = Annotated[
    TrialManagementService,
    Depends(_get_trial_management_service),
]


def _get_create_tenant_case(
    uow: GetUnitOfWork,
    security_service: GetSecurityService,
    register_service: Annotated[RegisterUserService, Depends(_get_register_user_service)],
    notifier_service: Annotated[
        WellcomeEmailService,
        Depends(get_wellcome_notifier_service),
    ],
    token_service: GetTokenService,
    trial_service: GetTrialManagementService,
) -> CreateTenantCase:
    return CreateTenantCase(
        uow=uow,
        security_service=security_service,
        register_service=register_service,
        notifier_service=notifier_service,
        token_service=token_service,
        trial_service=trial_service,
    )


def _get_login_user_case(
    uow: GetUnitOfWork,
    security_service: GetSecurityService,
    token_service: GetTokenService,
    login_service: Annotated[LoginUserService, Depends(_get_login_user_service)],
) -> LoginUserCase:
    return LoginUserCase(uow, security_service, token_service, login_service)


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
    security_service: GetSecurityService,
    change_password_service: Annotated[ChangePasswordService, Depends(_get_change_password_service)],
) -> ChangePasswordCase:
    return ChangePasswordCase(
        uow=uow,
        security_service=security_service,
        change_password_service=change_password_service,
    )


async def _get_current_user(
    uow: GetUnitOfWork,
    auth_service: "GetAuthService",
    token: "GetOauthToken",
    security_service: GetSecurityService,
) -> UserEntity:  # type: ignore[reportInvalidTypeForm]
    if not token:
        raise UnauthorizedError("No autorizado para realizar esta acción.")
    return await auth_service.get_authenticated_user(
        uow=uow,
        token=token.credentials,
    )


async def _get_current_tenant(
    uow: GetUnitOfWork,
    auth_service: "GetAuthService",
    token: "GetOauthToken",
) -> TenantEntity:  # type: ignore[reportInvalidTypeForm]
    """Resolve the current tenant from the JWT payload.

    Reads tenant_id from the access token, loads the TenantEntity via
    the tenant repository, and returns it. Raises UnauthorizedError if
    the token is missing or has no tenant_id.
    """
    if not token:
        raise UnauthorizedError("No autorizado para realizar esta acción.")

    payload = auth_service.token_service.decode(token.credentials)
    tid = payload.get("tenant_id")
    if not tid:
        raise UnauthorizedError("El token no contiene información de tenant.")

    async with uow as _uow:
        repo = _uow.get_repository(ITenantRepository)
        tenant = await repo.get_by_id(UUID(tid))  # type: ignore[attr-defined]
        if not tenant:
            raise UnauthorizedError("Tenant no encontrado.")
        return tenant


def require_role(min_role: UserRole):
    """Create a FastAPI Depends guard that enforces a minimum UserRole.

    Usage:
        @router.get("/protected", dependencies=[Depends(require_role(UserRole.EDITOR)])
        async def protected_endpoint(...): ...

    Raises NotPermissionError (HTTP 403) if current_user.role.rank < min_role.rank.
    """

    async def _role_checker(current_user: GetCurrentUser) -> None:
        if current_user.role.rank < min_role.rank:
            raise NotPermissionError(
                f"No tienes permisos suficientes. Se requiere rol '{min_role.value}' o superior.",
            )

    return Depends(_role_checker)


is_authenticated_current_user = Depends(_get_current_user)

GetOauthToken = Annotated[HTTPAuthorizationCredentials, Depends(_get_oauth_token)]
GetRefreshToken = Annotated[str, Depends(_get_refresh_token)]
GetAuthService = Annotated[AuthService, Depends(_get_auth_service)]
GetCurrentUser = Annotated[UserEntity, Depends(_get_current_user)]
GetCurrentTenant = Annotated[TenantEntity, Depends(_get_current_tenant)]
GetCreateTenantCase = Annotated[CreateTenantCase, Depends(_get_create_tenant_case)]
GetLoginUserCase = Annotated[LoginUserCase, Depends(_get_login_user_case)]
GetChangePasswordCase = Annotated[ChangePasswordCase, Depends(_get_change_password_case)]
GetLogoutUserCase = Annotated[LogoutUserCase, Depends(_get_logout_user_case)]
GetRefreshTokenCase = Annotated[RefreshTokenCase, Depends(_get_refresh_token_case)]
