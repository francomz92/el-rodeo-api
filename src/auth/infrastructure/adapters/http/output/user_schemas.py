from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserSchema(BaseModel):
    id: UUID
    created_at: datetime
    name: str
    dni: str

    model_config = ConfigDict(from_attributes=True)
