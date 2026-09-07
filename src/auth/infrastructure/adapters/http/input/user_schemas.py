"""Pydantic schemas for user profile HTTP input."""

from pydantic import BaseModel, EmailStr, Field


class UpdateProfileSchema(BaseModel):
    """Request body for PUT /users/me."""

    name: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
