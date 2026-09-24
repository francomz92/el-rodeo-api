from dataclasses import dataclass
from uuid import UUID


@dataclass
class TenantContext:
    tenant_id: UUID | None = None
    bypass_filter: bool = False
    current_user: object | None = None
