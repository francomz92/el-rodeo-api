from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection


class IAuditRepository(ABC):
    """Port for recording audit log entries.

    Implementations queue entries in-memory and flush them in bulk
    via a UoW before-commit hook, staying within the same transaction.
    """

    @abstractmethod
    def record(
        self,
        action: str,
        entity_type: str,
        entity_id: UUID,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        old_values: dict | None = None,
        new_values: dict | None = None,
        metadata: dict | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Record an audit entry in the in-memory queue.

        Entry is not persisted until flush() is called (typically via
        the UoW before_commit hook).
        """
        ...

    @abstractmethod
    async def flush(self, connection: AsyncConnection) -> None:
        """Persist all queued entries within the given transaction."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Drop queued entries without persisting (e.g. on rollback)."""
        ...

    @abstractmethod
    def queue_length(self) -> int:
        """Return the number of entries waiting to be flushed."""
        ...
