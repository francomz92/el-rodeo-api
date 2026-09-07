from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.infrastructure.adapters.http.output.animal_type_schemas import AnimalTypeSchema


class AnimalSchema(BaseModel):
    id: UUID
    type: AnimalTypeSchema | None = None
    caravana: str
    tag: str
    date_of_birth: date
    initial_weight: float
    initial_weight_date: date
    last_weight: float
    breed: str
    status: AnimalStatus

    model_config = ConfigDict(from_attributes=True)
