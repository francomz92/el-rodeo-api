from pydantic import BaseModel, Field


class AnimalTypeCretionSchema(BaseModel):
    name: str = Field(..., max_length=50)
