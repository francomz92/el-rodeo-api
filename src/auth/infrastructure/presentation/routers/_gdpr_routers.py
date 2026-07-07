"""GDPR compliance endpoints.

Allows users to export their data (GET /users/me/export) or request
anonymization (DELETE /users/me/data). Protected by require_role(VIEWER)
so any authenticated user can access their own data.
"""

from fastapi import APIRouter, status

from src.auth.domain.entities import UserRole
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCurrentUser,
    require_role,
)
from src.common.infrastructure.adapters.http.output.gdpr_schemas import (
    GDPRDeleteResponse,
    GDPRExportResponse,
)
from src.common.infrastructure.presentation.dependencies.gdpr import (
    GetGDPRDeleteService,
    GetGDPRExportService,
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
    gdpr_export_service: GetGDPRExportService,
) -> GDPRExportResponse:
    """Export all data for the current authenticated user."""
    data = await gdpr_export_service.export_user_data(current_user.id)
    if data is None:
        return GDPRExportResponse()
    return GDPRExportResponse(**data)


@gdpr_router.delete(
    path="/me/data",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Delete my data (GDPR)",
    description="Anonymizes all business records associated with the current "
    "user and disables the account. Audit log entries are preserved. "
    "Returns 202 Accepted as the operation may be processed asynchronously.",
    response_model=GDPRDeleteResponse,
    dependencies=[require_role(UserRole.VIEWER)],
)
async def delete_my_data(
    current_user: GetCurrentUser,
    gdpr_delete_service: GetGDPRDeleteService,
) -> GDPRDeleteResponse:
    """Request anonymization of all data for the current authenticated user.

    Business records are anonymized (user_id set to NULL), not deleted.
    The user account is disabled. Refresh tokens are revoked.
    Audit log entries are preserved as they are immutable by law.
    """
    await gdpr_delete_service.delete_user_data(current_user.id)
    return GDPRDeleteResponse()
