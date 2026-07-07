"""Pydantic schemas for GDPR endpoint responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GDPRUserProfileSchema(BaseModel):
    """User profile data for GDPR export (no password hash)."""

    id: UUID
    name: str
    dni: str
    email: str
    role: str
    created_at: datetime


class GDPRExportResponse(BaseModel):
    """Complete GDPR data export response."""

    user_profile: GDPRUserProfileSchema | None = None
    buyers: list[dict] = []
    sales: list[dict] = []
    animals: list[dict] = []
    animal_protocols: list[dict] = []
    purchases: list[dict] = []
    animal_supplies: list[dict] = []
    schedule_events: list[dict] = []
    audit_log: list[dict] = []

    model_config = ConfigDict(from_attributes=True)


class GDPRDeleteResponse(BaseModel):
    """Response for GDPR data deletion request."""

    message: str = "Your data deletion request has been accepted. Business records have been anonymized and your account has been disabled."
    status: str = "accepted"
