from uuid import UUID, uuid4

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from src.common.domain.repositories.audit_repository_port import IAuditRepository
from src.common.infrastructure.persistence.models import AuditLog
from src.common.utils.date_utils import get_current_datetime


def _json_safe(value: object) -> object:
    """Convert non-JSON-serializable values to strings.

    Handles UUID, datetime, date, and any other type that Python's
    JSON encoder cannot serialize (e.g. SQLAlchemy ``func.now()``).
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _json_safe_dict(values: dict | None) -> dict | None:
    """Recursively convert dict values to JSON-safe types."""
    if values is None:
        return None
    return {k: _json_safe(v) for k, v in values.items()}


class AuditRepository(IAuditRepository):
    """In-memory queue that accumulates audit entries and flushes them
    in bulk via SQLAlchemy Core INSERT within the same transaction.

    Connected to the UnitOfWork via a before_commit hook registered at
    UoW construction time.
    """

    def __init__(self) -> None:
        self._queue: list[dict] = []

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
        """Append a structured audit entry to the in-memory queue.

        Non-JSON-serializable values (UUID, datetime) in old_values,
        new_values, and metadata are converted to strings automatically.
        """
        self._queue.append(
            {
                "id": uuid4(),
                "tenant_id": tenant_id,
                "user_id": user_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "old_values": _json_safe_dict(old_values),
                "new_values": _json_safe_dict(new_values),
                "metadata": _json_safe_dict(metadata),
                "ip_address": ip_address,
                "created_at": get_current_datetime(),
            }
        )

    async def flush(self, connection: AsyncConnection) -> None:
        """Bulk-INSERT all queued entries and clear the queue.

        Uses raw SQLAlchemy Core DML on the audit_log table, consistent
        with the project's existing repository pattern.
        """
        if not self._queue:
            return

        stmt = insert(AuditLog.__table__).values(self._queue)  # type: ignore
        await connection.execute(stmt)
        self._queue.clear()

    def clear(self) -> None:
        """Drop queued entries without persisting (e.g. on rollback)."""
        self._queue.clear()

    def queue_length(self) -> int:
        """Return the number of entries waiting to be flushed."""
        return len(self._queue)
