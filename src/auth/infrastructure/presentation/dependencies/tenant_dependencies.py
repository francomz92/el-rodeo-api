from typing import Annotated

from fastapi import Depends

from src.auth.application.uses_cases.get_tenant_case import GetTenantCase
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_obtain_tenant_use_case(uow: GetUnitOfWork):
    return GetTenantCase(uow=uow)


GetObtainTenantCase = Annotated[GetTenantCase, Depends(_get_obtain_tenant_use_case)]
