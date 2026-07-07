"""Pydantic schemas for role management HTTP output."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserRoleResponseSchema(BaseModel):
    """Response schema for role update operations."""

    id: UUID
    name: str
    dni: str
    email: str
    role: str

    model_config = ConfigDict(from_attributes=True)
