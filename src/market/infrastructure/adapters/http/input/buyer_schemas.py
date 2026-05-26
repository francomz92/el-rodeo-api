from pydantic import BaseModel, Field

from src.common.infrastructure.adapters.http.input.query_params import StandardQueryParams


class BuyerListQueryParamsSchema(StandardQueryParams):
    name: str | None = Field(None, max_length=100)
    contact_number: str | None = Field(None, max_length=10)


class BuyerCreateSchema(BaseModel):
    name: str
    description: str
    contact_number: str
    contact_address: str


class BuyerUpdateSchema(BaseModel):
    name: str = Field(..., max_length=100, min_length=4)
    description: str | None = Field(None, max_length=500)
    contact_number: str | None = Field(None, max_length=10)
    contact_address: str | None = Field(None, max_length=100)
