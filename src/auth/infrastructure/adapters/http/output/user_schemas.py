from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserSchema(BaseModel):
    id: UUID
    created_at: datetime
    name: str
    dni: str
    email: str
    role: str
    is_active: bool
    tenant_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedUsersSchema(BaseModel):
    items: list[UserSchema]
    total: int
    page: int
    per_page: int
    has_next: bool = Field(
        default=False,
        description="Whether there are more pages after this one",
    )
