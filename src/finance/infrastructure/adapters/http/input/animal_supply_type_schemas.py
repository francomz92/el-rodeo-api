from pydantic import BaseModel, Field

from src.common.infrastructure.adapters.http.input.query_params import StandardQueryParams


class AnimalSupplyTypeListQueryParamsSchema(StandardQueryParams):
    name: str | None = Field(None, max_length=50)


class AnimalSupplyTypeCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class AnimalSupplyTypeUpdateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
