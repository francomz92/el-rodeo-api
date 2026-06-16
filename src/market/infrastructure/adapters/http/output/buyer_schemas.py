from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BuyerSchema(BaseModel):
    id: UUID
    name: str
    description: str
    contact_number: str
    contact_address: str

    model_config = ConfigDict(from_attributes=True)
