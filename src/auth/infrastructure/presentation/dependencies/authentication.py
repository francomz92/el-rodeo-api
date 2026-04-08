from typing import Annotated

from fastapi import Depends

from src.auth.application.services.authentication import AuthService
from src.auth.application.uses_cases.change_password import ChangePasswordCase
from src.auth.application.uses_cases.login_user import LoginUserCase
from src.auth.application.uses_cases.register_user import RegisterUserCase
from src.common.infrastructure.presentation.dependencies.security import GetSecurityService
from src.common.infrastructure.presentation.dependencies.token import GetTokenService
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_register_user_case(
    uow: GetUnitOfWork,
    security_service: GetSecurityService,
) -> RegisterUserCase:
    return RegisterUserCase(uow=uow, security_service=security_service)


def _get_login_user_case(
    uow: GetUnitOfWork,
    security_service: GetSecurityService,
    token_service: GetTokenService,
) -> LoginUserCase:
    return LoginUserCase(
        uow=uow,
        security_service=security_service,
        token_service=token_service,
    )


async def _get_auth_service(
    uow: GetUnitOfWork,
    token_service: GetTokenService,
) -> AuthService:
    return AuthService(token_service=token_service)


async def _get_change_password_case(
    uow: GetUnitOfWork,
    security_service: GetSecurityService,
    auth_service: "GetAuthService",
):
    return ChangePasswordCase(
        uow=uow,
        security_service=security_service,
        auth_service=auth_service,
    )


GetAuthService = Annotated[AuthService, Depends(_get_auth_service)]
GetRegisterUserCase = Annotated[RegisterUserCase, Depends(_get_register_user_case)]
GetLoginUserCase = Annotated[LoginUserCase, Depends(_get_login_user_case)]
GetChangePasswordCase = Annotated[ChangePasswordCase, Depends(_get_change_password_case)]
