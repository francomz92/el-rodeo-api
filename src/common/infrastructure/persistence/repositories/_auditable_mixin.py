"""AuditableRepositoryMixin — injectable audit helpers for repositories.

Usage:
    class MyRepo(IMyRepo, TenantAwareRepository, AuditableRepositoryMixin):
        async def create(self, data):
            entity = ...
            self._audit_create("MyEntity", entity.id, model_dump(entity))
            return entity

The UnitOfWork injects ``audit_repository``, ``current_user``, and
``tenant_id`` into each auditable repository after construction. The
mixin passes ``user_id`` and ``tenant_id`` to every recorded audit entry.
"""

from uuid import UUID

from src.common.domain.repositories.audit_repository_port import IAuditRepository


class AuditableRepositoryMixin:
    """Mixin that provides _audit_create / _audit_update / _audit_delete.

    Set ``audit_repository`` (IAuditRepository | None) before calling these
    methods. The UnitOfWork injects this, plus ``current_user`` and
    ``tenant_id``, automatically after construction.

    All methods are no-ops when ``audit_repository`` is None — safe for
    tests and mocks.
    """

    audit_repository: IAuditRepository | None = None
    current_user: object | None = None
    tenant_id: UUID | None = None

    # ── Helpers ──────────────────────────────────────────────────────────

    def _audit_context(self) -> dict:
        """Build the shared context dict for a record() call."""
        ctx: dict = {}
        if self.tenant_id is not None:
            ctx["tenant_id"] = self.tenant_id
        user_id = getattr(self.current_user, "id", None)
        if user_id is not None:
            ctx["user_id"] = user_id
        return ctx

    # ── Record helpers ───────────────────────────────────────────────────

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
        kws = {**self._audit_context(), **kwargs}
        self.audit_repository.record(
            action="create",
            entity_type=entity_type,
            entity_id=entity_id,
            new_values=new_values,
            **kws,
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
            **self._audit_context(),
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
            **self._audit_context(),
            **kwargs,
        )
