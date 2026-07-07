"""Dependency injection wiring for user management use cases."""

from typing import Annotated

from fastapi import Depends

from src.auth.application.uses_cases.get_user_by_id_case import GetUserByIdCase
from src.auth.application.uses_cases.get_user_profile_case import GetUserProfileCase
from src.auth.application.uses_cases.list_users_case import ListUsersCase
from src.auth.application.uses_cases.soft_delete_user_case import SoftDeleteUserCase
from src.auth.application.uses_cases.update_user_profile_case import UpdateUserProfileCase
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_user_profile_case() -> GetUserProfileCase:
    return GetUserProfileCase()


def _get_update_user_profile_case(
    uow: GetUnitOfWork,
) -> UpdateUserProfileCase:
    return UpdateUserProfileCase(uow=uow)


def _get_list_users_case(
    uow: GetUnitOfWork,
) -> ListUsersCase:
    return ListUsersCase(uow=uow)


def _get_soft_delete_user_case(
    uow: GetUnitOfWork,
) -> SoftDeleteUserCase:
    return SoftDeleteUserCase(uow=uow)


def _get_user_by_id_case(
    uow: GetUnitOfWork,
) -> GetUserByIdCase:
    return GetUserByIdCase(uow=uow)


GetUserProfileCaseDep = Annotated[
    GetUserProfileCase,
    Depends(_get_user_profile_case),
]

GetUpdateUserProfileCaseDep = Annotated[
    UpdateUserProfileCase,
    Depends(_get_update_user_profile_case),
]

GetListUsersCaseDep = Annotated[
    ListUsersCase,
    Depends(_get_list_users_case),
]

GetSoftDeleteUserCaseDep = Annotated[
    SoftDeleteUserCase,
    Depends(_get_soft_delete_user_case),
]

GetUserByIdCaseDep = Annotated[
    GetUserByIdCase,
    Depends(_get_user_by_id_case),
]
