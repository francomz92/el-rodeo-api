from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from src.cattle.domain.constants.animal import AnimalStatus



class AnimalCreationSchema(BaseModel):
    animal_type_id: UUID
    caravana: str = Field(..., max_length=50)
    name: str = Field(..., max_length=50)
    breed: str = Field(..., max_length=50)
    tag: str = Field(default_factory=str, max_length=50)
    date_of_birth: date
    initial_weight: float
    initial_weight_date: date
    status: AnimalStatus

