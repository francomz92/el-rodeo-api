"""Dependency injection wiring for role management use cases."""

from typing import Annotated

from fastapi import Depends

from src.auth.application.uses_cases.update_user_role_case import UpdateUserRoleCase
from src.auth.domain.services.update_user_role_service import UpdateUserRoleService
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
