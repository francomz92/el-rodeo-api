from pydantic import BaseModel


class BuyerSchema(BaseModel):
    id: str
    name: str
    description: str
    contact_number: str
    contact_address: str
