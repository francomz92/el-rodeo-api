from typing import Annotated

from fastapi import Depends
from fastapi.security.api_key import APIKeyHeader

from src.auth.application.services.authentication_service import AuthService
from src.auth.application.uses_cases.change_password_case import ChangePasswordCase
from src.auth.application.uses_cases.login_user_case import LoginUserCase
from src.auth.application.uses_cases.register_user_case import RegisterUserCase
from src.auth.domain.entities import UserEntity
from src.auth.domain.services.change_password_service import ChangePasswordService
from src.auth.domain.services.login_user_service import LoginUserService
from src.auth.domain.services.register_user_service import RegisterUserService
from src.common.infrastructure.presentation.dependencies.security import GetSecurityService
from src.common.infrastructure.presentation.dependencies.token import GetTokenService
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork

oauth2_scheme = APIKeyHeader(name="Authorization")


def _get_register_user_case(
    uow: GetUnitOfWork,
    security_service: GetSecurityService,
    register_service: Annotated[RegisterUserService, Depends()],
) -> RegisterUserCase:
    return RegisterUserCase(uow, security_service, register_service)


def _get_login_user_case(
    uow: GetUnitOfWork,
    security_service: GetSecurityService,
    token_service: GetTokenService,
    login_service: Annotated[LoginUserService, Depends()],
) -> LoginUserCase:
    return LoginUserCase(uow, security_service, token_service, login_service)


async def _get_auth_service(token_service: GetTokenService) -> AuthService:
    return AuthService(token_service=token_service)


async def _get_change_password_case(
    uow: GetUnitOfWork,
    security_service: GetSecurityService,
    auth_service: "GetAuthService",
    change_password_service: Annotated[ChangePasswordService, Depends()],
):
    return ChangePasswordCase(
        uow,
        security_service,
        auth_service,
        change_password_service,
    )


async def _get_current_user(
    uow: GetUnitOfWork,
    auth_service: "GetAuthService",
    token: Annotated[str, Depends(oauth2_scheme)],
):
    return await auth_service.get_authenticated_user(uow=uow, token=token)


GetAuthService = Annotated[AuthService, Depends(_get_auth_service)]
GetCurrentUser = Annotated[UserEntity, Depends(_get_current_user)]
GetRegisterUserCase = Annotated[RegisterUserCase, Depends(_get_register_user_case)]
GetLoginUserCase = Annotated[LoginUserCase, Depends(_get_login_user_case)]
GetChangePasswordCase = Annotated[ChangePasswordCase, Depends(_get_change_password_case)]
