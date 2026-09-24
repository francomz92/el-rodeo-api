"""Dependency injection wiring for role management use cases."""

from typing import Annotated

from fastapi import Depends

from src.auth.application.uses_cases.invite_user_case import InviteUserCase
from src.auth.application.uses_cases.update_user_role_case import UpdateUserRoleCase
from src.auth.domain.services.register_user_service import RegisterUserService
from src.auth.domain.services.update_user_role_service import UpdateUserRoleService
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    _get_register_user_service,
)
from src.common.infrastructure.events.handlers.email_notification import EmailNotificationHandler
from src.common.infrastructure.presentation.dependencies.event_bus import GetEventBus
from src.common.infrastructure.presentation.dependencies.notifier import GetNotifierClient
from src.common.infrastructure.presentation.dependencies.security import (
    GetSecurityService,
)
from src.common.infrastructure.presentation.dependencies.token import GetTokenService
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_update_user_role_case(
    uow: GetUnitOfWork,
) -> UpdateUserRoleCase:
    return UpdateUserRoleCase(
        uow=uow,
        update_user_role_service=UpdateUserRoleService(),
    )


GetUpdateUserRoleCase = Annotated[
    UpdateUserRoleCase,
    Depends(_get_update_user_role_case),
]


def _get_invite_user_case(
    uow: GetUnitOfWork,
    security_service: GetSecurityService,
    register_service: Annotated[RegisterUserService, Depends(_get_register_user_service)],
    bus: GetEventBus,
    notifier: GetNotifierClient,
    token_service: GetTokenService,
) -> InviteUserCase:
    bus.register("user.registered", EmailNotificationHandler(notifier))
    return InviteUserCase(
        uow=uow,
        security_service=security_service,
        register_service=register_service,
        event_bus=bus,
        token_service=token_service,
    )


GetInviteUserCase = Annotated[
    InviteUserCase,
    Depends(_get_invite_user_case),
]
