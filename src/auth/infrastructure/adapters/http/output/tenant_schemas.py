from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.billing.infrastructure.adapters.http.output.plan_schemas import PlanResponseSchema


class TenantResponseSchema(BaseModel):
    id: UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime
    plan: PlanResponseSchema | None = None
