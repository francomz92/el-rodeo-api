"""Dependency injection wiring for GDPR use cases."""

from typing import Annotated

from fastapi import Depends

from src.common.application.uses_cases.gdpr_cases.delete_user_data_case import (
    GDPRDeleteUserDataCase,
)
from src.common.application.uses_cases.gdpr_cases.export_user_data_case import (
    GDPRExportUserDataCase,
)

from .uow import GetUnitOfWork


def _get_gdpr_delete_user_data_case(
    uow: GetUnitOfWork,
) -> GDPRDeleteUserDataCase:
    return GDPRDeleteUserDataCase(uow=uow)


def _get_gdpr_export_user_data_case(
    uow: GetUnitOfWork,
) -> GDPRExportUserDataCase:
    return GDPRExportUserDataCase(uow=uow)


GetGDPRDeleteUserDataCase = Annotated[
    GDPRDeleteUserDataCase,
    Depends(_get_gdpr_delete_user_data_case),
]

GetGDPRExportUserDataCase = Annotated[
    GDPRExportUserDataCase,
    Depends(_get_gdpr_export_user_data_case),
]
