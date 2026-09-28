from uuid import UUID

from src.auth.domain.repositories.tenant_plan_reader_port import ITenantPlanReader
from src.auth.domain.repositories.tenant_repository_port import ITenantRepository
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotFoundError


class GetTenantCase:
    def __init__(self, uow: IUoW):
        self.uow = uow

    async def execute(self, tenant_id: UUID | None):
        if not tenant_id:
            raise NotFoundError("Este usuario no pertenece a ninguna organización")
        async with self.uow as uow:
            repository = uow.get_repository(ITenantRepository)
            tenant = await repository.get_by_id(tenant_id)
            if not tenant:
                raise NotFoundError("No se encontró el la organización con el id proporcionado")
            if tenant.plan_id is not None:
                plan_reader = uow.get_repository(ITenantPlanReader)
                tenant.plan = await plan_reader.get_by_id(tenant.plan_id)
            return tenant
