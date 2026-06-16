from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SupplyTypeSchema(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)
