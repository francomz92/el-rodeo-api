from collections.abc import Mapping
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.application.ports.uow import IRepository
from src.common.domain.repositories.audit_repository_port import IAuditRepository
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)


class RepositoryFactory:
    """Construct repositories and inject their UnitOfWork context."""

    @staticmethod
    def create(
        repository_type: type[IRepository],
        repositories: Mapping[type[IRepository], type[IRepository]],
        session: AsyncSession,
        tenant_id: UUID | None,
        bypass_filter: bool,
        audit_repository: IAuditRepository,
        current_user: object | None,
    ) -> IRepository:
        repository = repositories.get(repository_type, None)
        if not repository:
            raise ValueError(f"Repository of type {repository_type} not found.")

        repo_init_kws: dict[str, object] = {"session": session}
        if issubclass(repository, TenantAwareRepository):
            repo_init_kws["tenant_id"] = tenant_id
            repo_init_kws["bypass_filter"] = bypass_filter

        repo = repository(**repo_init_kws)

        if isinstance(repo, AuditableRepositoryMixin):
            repo.audit_repository = audit_repository
            repo.current_user = current_user
            repo.tenant_id = tenant_id

        return repo
