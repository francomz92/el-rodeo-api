from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from src.common.infrastructure.adapters.http.input.query_params import StandardQueryParams


class BuyerListQueryParamsSchema(StandardQueryParams):
    ALLOWED_ORDER_BY: ClassVar[frozenset[str]] = frozenset({"name", "created_at"})

    order_by: Literal["name", "created_at"] = Field(
        default="created_at",
        max_length=50,
        description="List ordering",
    )
    name: str | None = Field(None, max_length=100)
    contact_number: str | None = Field(None, max_length=10)


class BuyerCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)
    contact_number: str = Field(..., max_length=10)
    contact_address: str = Field(..., max_length=100)


class BuyerUpdateSchema(BaseModel):
    name: str | None = Field(None, max_length=100, min_length=4)
    description: str | None = Field(None, max_length=500)
    contact_number: str | None = Field(None, max_length=10)
    contact_address: str | None = Field(None, max_length=100)
