"""Pydantic schemas for role management HTTP input."""

from pydantic import BaseModel, Field, field_validator

from src.auth.domain.entities._user_role import UserRole


class UpdateRoleSchema(BaseModel):
    """Request body for PUT /users/{id}/role."""

    role: UserRole = Field(
        ...,
        description="New role for the user: viewer, editor, admin, or owner",
    )

    @field_validator("role")
    @classmethod
    def reject_super_admin(cls, role: UserRole) -> UserRole:
        """Reject SUPER_ADMIN — cannot be assigned via the public API."""
        if role == UserRole.SUPER_ADMIN:
            raise ValueError("SUPER_ADMIN no puede asignarse a través de la API pública")
        return role
