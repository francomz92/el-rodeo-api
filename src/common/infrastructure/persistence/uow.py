import dataclasses
from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.application.ports.uow import IRepository, IUoW, IUoWFactory
from src.common.domain.events.base import DomainEvent
from src.common.infrastructure.persistence.connections.db import AsyncSessionMaker
from src.common.infrastructure.persistence.models.event_outbox import EventOutbox
from src.common.infrastructure.persistence.repositories.audit_repository import (
    AuditRepository,
)

from .repositories import repositories_list
from .repository_factory import RepositoryFactory
from .tenant_context import TenantContext


def _serialize_event(event: DomainEvent) -> dict:
    """Serialise *event* to a JSON-safe dict including subclass-specific fields.

    Uses ``dataclasses.asdict`` so fields added by subclasses (e.g.
    ``PaymentReceived.payment_id``) are automatically included in the
    outbox payload rather than being silently dropped.
    """
    raw = dataclasses.asdict(event)
    return {k: (str(v) if isinstance(v, (UUID, datetime)) else v) for k, v in raw.items()}


class UnitOfWork(IUoW):
    db: AsyncSession
    audit_repository: AuditRepository

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: UUID | None = None,
        bypass_filter: bool = False,
        current_user: object | None = None,
    ) -> None:
        self.db = session
        self.tenant_context = TenantContext(
            tenant_id=tenant_id,
            bypass_filter=bypass_filter,
            current_user=current_user,
        )
        self._before_commit_hooks: list[Callable[[], None]] = []
        self.outbox_events: list[DomainEvent] = []
        self.audit_repository = AuditRepository()

    @property
    def tenant_id(self) -> UUID | None:
        return self.tenant_context.tenant_id

    @tenant_id.setter
    def tenant_id(self, value: UUID | None) -> None:
        self.tenant_context.tenant_id = value

    @property
    def bypass_filter(self) -> bool:
        return self.tenant_context.bypass_filter

    @bypass_filter.setter
    def bypass_filter(self, value: bool) -> None:
        self.tenant_context.bypass_filter = value

    @property
    def current_user(self) -> object | None:
        return self.tenant_context.current_user

    @current_user.setter
    def current_user(self, value: object | None) -> None:
        self.tenant_context.current_user = value

    async def _do_audit_flush(self) -> None:
        """Flush queued audit entries within the current transaction."""
        if self.audit_repository.queue_length() > 0:
            conn = await self.db.connection()
            await self.audit_repository.flush(conn)

    def _flush_outbox_events(self) -> None:
        """Serialize queued domain events and persist them to the outbox table.

        Called from ``commit()`` after audit flush and before
        ``db.commit()``.  Each ``DomainEvent`` is serialised to a
        JSON-safe dict (including subclass-specific fields via
        ``dataclasses.asdict``), wrapped in an ``EventOutbox`` model
        instance, and added to the current session.  The in-memory
        queue is cleared after all rows are inserted.

        If no events are queued, this is a no-op.
        """
        for event in self.outbox_events:
            payload = _serialize_event(event)
            outbox_row = EventOutbox(
                event_id=event.event_id,
                event_type=event.event_type,
                aggregate_id=event.aggregate_id,
                payload=payload,
            )
            self.db.add(outbox_row)
        self.outbox_events.clear()

    def get_repository(self, repository_type: type[IRepository]) -> IRepository:
        return RepositoryFactory.create(
            repository_type=repository_type,
            repositories=repositories_list,
            session=self.db,
            tenant_context=self.tenant_context,
            audit_repository=self.audit_repository,
        )

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
        await self.db.rollback()

    async def refresh(self, entity):
        await self.db.refresh(entity)

    async def dispose(self):
        await self.db.close()

    def add_before_commit_hook(self, hook: Callable[[], None]) -> None:
        """Register a hook to execute before db.commit(), in FIFO order."""
        self._before_commit_hooks.append(hook)

    def add_outbox_event(self, event: DomainEvent) -> None:
        """Queue *event* for transactional outbox persistence."""
        self.outbox_events.append(event)


class UnitOfWorkFactory(IUoWFactory):
    """Creates a UnitOfWork with its own database session.

    Each call to ``__call__`` creates a new ``AsyncSession`` via the
    project's async session maker, ensuring the returned UoW has a
    session that is **not** tied to any request lifecycle.
    """

    def __call__(self) -> UnitOfWork:
        """Create a new ``UnitOfWork`` with a fresh async session."""
        return UnitOfWork(session=AsyncSessionMaker())
