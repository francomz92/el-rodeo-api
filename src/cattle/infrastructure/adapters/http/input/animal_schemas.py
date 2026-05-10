from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.cattle.domain.constants.animal import AnimalStatus
from src.common.infrastructure.adapters.http.input.query_params import StandardQueryParams


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
    caravana: Optional[str]
    name: Optional[str]
    date_of_birth: Optional[date]
    initial_weight: Optional[float]
    initial_weight_date: Optional[date]
    last_weight: Optional[float]
    breed: Optional[str]
    tag: Optional[str]
    status: Optional[AnimalStatus]


class AnimalsListQueryParamsSchema(StandardQueryParams):
    type_id: Optional[UUID] = None
    caravana: Optional[str] = Field(default=None, max_length=50, description="Identifier of animal")
    name: Optional[str] = Field(default=None, max_length=50, description="Name of animal")
    breed: Optional[str] = Field(default=None, max_length=50, description="Breed of animal")
