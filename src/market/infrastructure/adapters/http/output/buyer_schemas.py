from uuid import UUID

from pydantic import BaseModel


class BuyerSchema(BaseModel):
    id: UUID
    name: str
    description: str
    contact_number: str
    contact_address: str
