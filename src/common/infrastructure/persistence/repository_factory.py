from collections.abc import Callable, Mapping
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.application.ports.uow import IRepository
from src.common.domain.repositories.audit_repository_port import IAuditRepository
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)
from src.common.infrastructure.persistence.tenant_context import TenantContext


class RepositoryFactory:
    """Construct repositories and inject their UnitOfWork context."""

    @staticmethod
    def create(
        repository_type: type[IRepository],
        repositories: Mapping[type[IRepository], type[IRepository]],
        session: AsyncSession,
        tenant_context: TenantContext,
        audit_repository: IAuditRepository,
    ) -> IRepository:
        repository = repositories.get(repository_type, None)
        if not repository:
            raise ValueError(f"Repository of type {repository_type} not found.")

        repo_init_kws: dict[str, object] = {"session": session}
        if issubclass(repository, TenantAwareRepository):
            repo_init_kws["tenant_id"] = tenant_context.tenant_id
            repo_init_kws["bypass_filter"] = tenant_context.bypass_filter

        # The registry maps interfaces to concrete repositories with different
        # constructor kwargs; their shared constructor contract is established by
        # registry configuration rather than the IRepository protocol.
        repository_constructor = cast(Callable[..., IRepository], repository)
        repo = repository_constructor(**repo_init_kws)

        if isinstance(repo, AuditableRepositoryMixin):
            repo.audit_repository = audit_repository
            repo.current_user = tenant_context.current_user
            repo.tenant_id = tenant_context.tenant_id

        return repo
