"""Mock implementations of infrastructure ports for unit testing.

These mocks replace the real UnitOfWork and repositories so that use case
tests can run without a database connection. They implement the port interfaces
directly without relying on MagicMock inheritance.
"""

from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock

from src.common.domain.events.base import DomainEvent
from src.common.domain.repository import IRepository
from src.common.infrastructure.persistence.repositories.audit_repository import (
    AuditRepository,
)


class MockRepository:
    """A fake repository that returns AsyncMock for every interface method.

    Usage:
        repo = MockRepository()
        repo.create.return_value = some_entity
    """

    def __init__(self) -> None:
        self._async_mocks: dict[str, AsyncMock] = {}

    def __getattr__(self, name: str) -> Any:
        """Return a cached AsyncMock for any attribute access.

        This allows the mock to satisfy any repository interface without
        pre-declaring every method.
        """
        if name.startswith("_") or name in ("__init__",):
            raise AttributeError(name)
        if name not in self._async_mocks:
            self._async_mocks[name] = AsyncMock()
        return self._async_mocks[name]


class MockUoW:
    """A fake Unit of Work that returns a MockRepository for any requested type.

    Usage:
        uow = MockUoW()
        uow.get_repository(ISalesRepository).create.return_value = sale_entity

        case = CreateSaleCase(uow, service)
        result = await case.execute(data)

    Supports tenant_id attribute for multi-tenancy scenarios.
    Supports before_commit hooks and audit repository for audit testing.
    """

    def __init__(self, tenant_id=None) -> None:
        self._repos: dict[type[IRepository], MockRepository] = {}
        self.tenant_id = tenant_id
        self.bypass_filter = False
        self.current_user: object | None = None
        self._before_commit_hooks: list[Callable[[], None]] = []
        self.audit_repository = AuditRepository()
        self.outbox_events: list[DomainEvent] = []
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.refresh = AsyncMock()
        self.dispose = AsyncMock()

    def add_before_commit_hook(self, hook: Callable[[], None]) -> None:
        """Register a hook to execute before commit."""
        self._before_commit_hooks.append(hook)

    def add_outbox_event(self, event: DomainEvent) -> None:
        """Queue event for transactional outbox persistence."""
        self.outbox_events.append(event)

    def get_repository(self, repo_type: type[IRepository]) -> MockRepository:
        """Return a cached MockRepository for the given interface type."""
        if repo_type not in self._repos:
            self._repos[repo_type] = MockRepository()
        return self._repos[repo_type]

    async def __aenter__(self) -> "MockUoW":
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass
