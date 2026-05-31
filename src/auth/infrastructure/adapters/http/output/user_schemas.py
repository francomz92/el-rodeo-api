from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserSchema(BaseModel):
    id: UUID
    created_at: datetime
    name: str
    dni: str
