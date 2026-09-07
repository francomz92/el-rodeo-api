from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.domain.events.base import DomainEvent
from src.common.domain.repositories.audit_repository_port import IAuditRepository
from src.common.domain.repository import IRepository

RepositoryType = TypeVar("RepositoryType", bound=IRepository)


@dataclass
class IUoW(ABC):
    db: AsyncSession | None = None
    bypass_filter: bool = False
    current_user: object | None = None
    tenant_id: UUID | None = None
    audit_repository: IAuditRepository | None = None
    outbox_events: list[DomainEvent] = field(default_factory=list)

    @abstractmethod
    async def __aenter__(self) -> "IUoW":
        """Método de entrada para el context manager asíncrono."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Método de salida para el context manager asíncrono."""
        pass

    @abstractmethod
    def get_repository(self, repository_type: type[RepositoryType]) -> RepositoryType:
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def refresh(self, entity) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def dispose(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_before_commit_hook(self, hook: Callable[[], None]) -> None:
        """Register a hook to execute before db.commit(), in FIFO order.

        If any hook raises, the transaction is rolled back and the
        exception propagates.
        """
        raise NotImplementedError

    @abstractmethod
    def add_outbox_event(self, event: DomainEvent) -> None:
        """Queue *event* for transactional outbox persistence.

        The event is flushed to the ``event_outbox`` table during
        ``commit()`` and later consumed by a background forwarder.
        """
        raise NotImplementedError


class IUoWFactory(ABC):
    """Factory that creates an IUoW with its own database session.

    Use this when work needs its own session context — for example,
    background tasks, workers, or any flow that runs outside the
    FastAPI request lifecycle.

    Usage::

        uow = factory()
        async with uow:
            repo = uow.get_repository(IRepository)
            ...
            await uow.commit()
    """

    @abstractmethod
    def __call__(self) -> IUoW:
        """Create a new IUoW with a fresh database session."""
        ...
