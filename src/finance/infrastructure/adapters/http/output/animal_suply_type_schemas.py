from uuid import UUID

from pydantic import BaseModel


class SupplyTypeSchema(BaseModel):
    id: UUID
    name: str
