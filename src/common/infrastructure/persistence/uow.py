from collections.abc import Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.application.ports.uow import IRepository, IUoW
from src.common.domain.events.base import DomainEvent
from src.common.infrastructure.persistence.models.event_outbox import EventOutbox
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.audit_repository import (
    AuditRepository,
)

from .repositories import repositories_list
from .repositories.tenant_aware_repository import TenantAwareRepository


class UnitOfWork(IUoW):
    db: AsyncSession
    audit_repository: AuditRepository

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: UUID | None = None,
        current_user: object | None = None,
    ) -> None:
        self.db = session
        self.tenant_id = tenant_id
        self.bypass_filter = False
        self.current_user = current_user
        self._before_commit_hooks: list[Callable[[], None]] = []
        self.outbox_events: list[DomainEvent] = []
        self.audit_repository = AuditRepository()
        self._wire_audit_repository()

    def _wire_audit_repository(self) -> None:
        """AuditRepository flush is called directly in commit() — no hook needed."""
        pass

    async def _do_audit_flush(self) -> None:
        """Flush queued audit entries within the current transaction."""
        if self.audit_repository.queue_length() > 0:
            conn = await self.db.connection()
            await self.audit_repository.flush(conn)

    def _flush_outbox_events(self) -> None:
        """Serialize queued domain events and persist them to the outbox table.

        Called from ``commit()`` after audit flush and before
        ``db.commit()``.  Each ``DomainEvent`` is serialised to a
        JSON-safe dict, wrapped in an ``EventOutbox`` model instance,
        and added to the current session.  The in-memory queue is
        cleared after all rows are inserted.

        If no events are queued, this is a no-op.
        """
        for event in self.outbox_events:
            outbox_row = EventOutbox(
                event_id=event.event_id,
                event_type=event.event_type,
                aggregate_id=event.aggregate_id,
                payload={
                    "event_id": str(event.event_id),
                    "aggregate_id": str(event.aggregate_id),
                    "event_type": event.event_type,
                    "timestamp": event.timestamp.isoformat(),
                    "metadata": event.metadata,
                },
            )
            self.db.add(outbox_row)
        self.outbox_events.clear()

    def get_repository(self, repository_type: type[IRepository]) -> IRepository:
        repository = repositories_list.get(repository_type, None)
        if not repository:
            raise ValueError(f"Repository of type {repository_type} not found.")
        if issubclass(repository, TenantAwareRepository):
            repo = repository(
                self.db,
                self.tenant_id,
                bypass_filter=self.bypass_filter,
            )  # type: ignore
        else:
            repo = repository(self.db)  # type: ignore

        # Inject audit_repository into mixin-enabled repositories
        if isinstance(repo, AuditableRepositoryMixin):
            repo.audit_repository = self.audit_repository

        return repo  # type: ignore[return-value]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, *args, **kwargs):
        if exc_type:
            await self.rollback()
        await self.dispose()

    async def commit(self):
        """Execute before_commit hooks, flush audit, then commit.

        Hooks execute in FIFO order. If any hook raises, the transaction
        is rolled back and the exception propagates.
        """
        try:
            for hook in self._before_commit_hooks:
                hook()
        except Exception:
            await self.rollback()
            raise

        await self._do_audit_flush()
        self._flush_outbox_events()
        await self.db.commit()

    async def rollback(self):
        self.audit_repository.clear()
        self.outbox_events.clear()
        self._pending_audit_flush = False
        await self.db.rollback()

    async def refresh(self, entity):
        await self.db.refresh(entity)

    async def dispose(self):
        await self.db.close()

    def add_before_commit_hook(self, hook: Callable[[], None]) -> None:
        """Register a hook to execute before db.commit(), in FIFO order."""
        self._before_commit_hooks.append(hook)
