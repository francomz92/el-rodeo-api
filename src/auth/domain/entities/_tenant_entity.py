from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.billing.domain.entities import PlanEntity


@dataclass
class TenantEntity:
    id: UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime
    plan: PlanEntity | None = None
