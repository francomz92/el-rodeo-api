from uuid import UUID

from pydantic import BaseModel, Field

from src.common.infrastructure.adapters.http.input.query_params import StandardQueryParams


class AnimalTypeListQueryParamsSchema(StandardQueryParams):
    id: UUID | None = None
    name: str | None = Field(None, max_length=50)


class AnimalTypeCreateSchema(BaseModel):
    name: str = Field(..., max_length=50)


class AnimalTypeUpdateSchema(BaseModel):
    name: str = Field(..., max_length=50)
