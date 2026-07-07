from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from src.common.utils.date_utils import get_current_datetime


@dataclass
class AuditLogEntry:
    """Immutable audit log entry representing a single CUD operation.

    Created before the DB commit, persisted in the same transaction via
    the AuditRepository queue+flush mechanism. Fields map 1:1 to the
    audit_log table columns.
    """

    id: UUID
    entity_id: UUID
    tenant_id: UUID | None = None
    user_id: UUID | None = None
    action: str = ""
    entity_type: str = ""
    old_values: dict | None = None
    new_values: dict | None = None
    ip_address: str | None = None
    metadata: dict | None = None
    created_at: datetime = field(default_factory=get_current_datetime)
