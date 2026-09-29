"""GDPR compliance endpoints.

Allows users to export their data (GET /users/me/export). The former
self-service DELETE /users/me/data route is retired: data unlinking is
performed by tenant administrators through the guarded soft-delete flow.
Protected by require_role(VIEWER) so any authenticated user can access
their own data.
"""

from fastapi import APIRouter, status

from src.auth.domain.entities import UserRole
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCurrentUser,
    require_role,
)
from src.common.infrastructure.adapters.http.output.gdpr_schemas import (
    GDPRExportResponse,
)
from src.common.infrastructure.presentation.dependencies.gdpr import (
    GetGDPRExportUserDataCase,
)

gdpr_router = APIRouter()


@gdpr_router.get(
    path="/me/export",
    status_code=status.HTTP_200_OK,
    summary="Export my data (GDPR)",
    description="Returns all personal data associated with the current user across all contexts. Password hashes are never included.",
    response_model=GDPRExportResponse,
    dependencies=[require_role(UserRole.VIEWER)],
)
async def export_my_data(
    current_user: GetCurrentUser,
    gdpr_export_case: GetGDPRExportUserDataCase,
) -> GDPRExportResponse:
    """Export all data for the current authenticated user."""
    data = await gdpr_export_case.execute(current_user.id)
    if data is None:
        return GDPRExportResponse()
    return GDPRExportResponse(**data)
