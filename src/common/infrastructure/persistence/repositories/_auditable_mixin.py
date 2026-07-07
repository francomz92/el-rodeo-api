"""AuditableRepositoryMixin — injectable audit helpers for repositories.

Usage:
    class MyRepo(IMyRepo, TenantAwareRepository, AuditableRepositoryMixin):
        async def create(self, data):
            entity = ...
            self._audit_create("MyEntity", entity.id, model_dump(entity))
            return entity

The UnitOfWork injects `audit_repository` into each repository after construction.
All methods are no-ops when `audit_repository` is None (safe for tests / mocks).
"""

from uuid import UUID

from src.common.domain.repositories.audit_repository_port import IAuditRepository


class AuditableRepositoryMixin:
    """Mixin that provides _audit_create / _audit_update / _audit_delete.

    Set `audit_repository` (IAuditRepository | None) before calling these
    methods. The UnitOfWork does this automatically after construction.
    """

    audit_repository: IAuditRepository | None = None

    def _audit_create(
        self,
        entity_type: str,
        entity_id: UUID,
        new_values: dict | None = None,
        **kwargs,
    ) -> None:
        """Record a 'create' audit entry for the given entity."""
        if self.audit_repository is None:
            return
        self.audit_repository.record(
            action="create",
            entity_type=entity_type,
            entity_id=entity_id,
            new_values=new_values,
            **kwargs,
        )

    def _audit_update(
        self,
        entity_type: str,
        entity_id: UUID,
        old_values: dict | None = None,
        new_values: dict | None = None,
        **kwargs,
    ) -> None:
        """Record an 'update' audit entry for the given entity."""
        if self.audit_repository is None:
            return
        self.audit_repository.record(
            action="update",
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            **kwargs,
        )

    def _audit_delete(
        self,
        entity_type: str,
        entity_id: UUID,
        old_values: dict | None = None,
        **kwargs,
    ) -> None:
        """Record a 'delete' audit entry for the given entity."""
        if self.audit_repository is None:
            return
        self.audit_repository.record(
            action="delete",
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            **kwargs,
        )
