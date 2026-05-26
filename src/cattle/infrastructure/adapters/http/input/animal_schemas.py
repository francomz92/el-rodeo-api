from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from src.cattle.domain.constants.animal import AnimalStatus
from src.common.infrastructure.adapters.http.input.query_params import StandardQueryParams


class AnimalsListQueryParamsSchema(StandardQueryParams):
    type_id: UUID | None = None
    caravana: str | None = Field(default=None, max_length=50, description="Identifier of animal")
    name: str | None = Field(default=None, max_length=50, description="Name of animal")
    breed: str | None = Field(default=None, max_length=50, description="Breed of animal")


class AnimalCreationSchema(BaseModel):
    type_id: UUID
    caravana: str = Field(..., max_length=50)
    name: str = Field(..., max_length=50)
    breed: str = Field(..., max_length=50)
    tag: str = Field(default_factory=str, max_length=50)
    date_of_birth: date
    initial_weight: float
    initial_weight_date: date


class AnimalUpdateSchema(BaseModel):
    type_id: UUID
    caravana: str | None = None
    name: str | None = None
    date_of_birth: date | None = None
    initial_weight: float | None = None
    initial_weight_date: date | None = None
    last_weight: float | None = None
    breed: str | None = None
    tag: str | None = None
    status: AnimalStatus | None = None
