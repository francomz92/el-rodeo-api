"""Pydantic schemas for role management HTTP input."""

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.auth.domain.entities._user_role import UserRole


class InviteSchema(BaseModel):
    """Request body for POST /auth/invite."""

    name: str = Field(..., max_length=50)
    dni: str = Field(..., max_length=10)
    email: EmailStr
    role: UserRole

    @field_validator("role")
    @classmethod
    def reject_owner_and_super_admin(cls, role: UserRole) -> UserRole:
        """Reject OWNER and SUPER_ADMIN — cannot be assigned via invite."""
        if role in (UserRole.OWNER, UserRole.SUPER_ADMIN):
            raise ValueError("No se puede invitar con rol OWNER o SUPER_ADMIN")
        return role


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
