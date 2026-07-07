from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class TenantEntity:
    id: UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime
    plan_id: UUID | None = None
