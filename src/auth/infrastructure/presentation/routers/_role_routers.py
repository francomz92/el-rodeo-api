"""Router for role management endpoints.

Only OWNER-level users can access these endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse

from src.auth.domain.entities import UserRole
from src.auth.infrastructure.adapters.http.input.role_schemas import UpdateRoleSchema
from src.auth.infrastructure.adapters.http.output.role_schemas import (
    UserRoleResponseSchema,
)
from src.auth.infrastructure.adapters.http.output.user_schemas import (
    PaginatedUsersSchema,
    UserSchema,
)
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCurrentUser,
    require_role,
)
from src.auth.infrastructure.presentation.dependencies.role_dependencies import (
    GetUpdateUserRoleCase,
)
from src.auth.infrastructure.presentation.dependencies.user_dependencies import (
    GetListUsersCaseDep,
    GetSoftDeleteUserCaseDep,
    GetUserByIdCaseDep,
)
from src.common.infrastructure.adapters.http.output.cursor_page import (
    CursorPage,
    encode_cursor,
)
from src.common.infrastructure.adapters.http.output.messages import (
    SimpleMessageSchema,
)

role_router = APIRouter()


@role_router.put(
    path="/{user_id}/role",
    status_code=status.HTTP_200_OK,
    summary="Update a user's role",
    description="Only OWNER-level users can change roles. Self-escalation and last-OWNER demotion are blocked.",
    response_model=UserRoleResponseSchema,
    dependencies=[require_role(UserRole.OWNER)],
)
async def update_user_role(
    user_id: UUID,
    data: UpdateRoleSchema,
    current_user: GetCurrentUser,
    update_user_role_case: GetUpdateUserRoleCase,
) -> UserRoleResponseSchema:
    """Update a user's role.

    Business rules are enforced by UpdateUserRoleCase:
    - Only OWNER can change roles
    - Cannot change own role (self-escalation prevention)
    - Cannot demote the last OWNER in the tenant
    - Cross-tenant isolation
    """
    updated_user = await update_user_role_case.execute(
        actor=current_user,
        target_user_id=user_id,
        new_role=data.role,
    )
    return UserRoleResponseSchema(
        id=updated_user.id,
        name=updated_user.name,
        dni=updated_user.dni,
        email=updated_user.email,
        role=updated_user.role.value,
    )


@role_router.get(
    path="",
    status_code=status.HTTP_200_OK,
    summary="List users (admin)",
    description="Requires ADMIN or higher role. Tenant-scoped.",
    response_model=PaginatedUsersSchema,
    dependencies=[require_role(UserRole.ADMIN)],
)
async def list_users(
    current_user: GetCurrentUser,
    list_users_case: GetListUsersCaseDep,
    page: int = Query(default=1, ge=1, description="Page number (deprecated, use cursor)"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(default=None, description="Search by name or email"),
    role: UserRole | None = Query(default=None, description="Filter by role"),
    cursor: str | None = Query(default=None, description="Cursor for cursor-based pagination"),
):
    """List users for the current tenant with pagination and optional filters."""
    users, total, next_cursor = await list_users_case.execute(
        current_user=current_user,
        page=page,
        per_page=per_page,
        search=search,
        role=role,
        cursor=cursor,
    )

    if cursor is not None:
        # Return cursor-paginated response (bypasses response_model validation)
        user_items = [
            UserSchema(
                id=u.id,
                created_at=u.created_at,
                name=u.name,
                dni=u.dni,
                email=u.email,
                role=u.role.value,
                is_active=u.is_active,
                tenant_id=u.tenant_id,
            )
            for u in users
        ]
        page_data = CursorPage[UserSchema](
            items=user_items,
            cursor=encode_cursor(str(user_items[0].id), sort_value=user_items[0].created_at.isoformat()) if user_items else None,
            next_cursor=next_cursor,
            total=total,
        )
        return JSONResponse(
            content=page_data.model_dump(mode="json"),
            status_code=status.HTTP_200_OK,
        )

    return PaginatedUsersSchema(  # type: ignore[return-type]
        items=[
            UserSchema(
                id=u.id,
                created_at=u.created_at,
                name=u.name,
                dni=u.dni,
                email=u.email,
                role=u.role.value,
                is_active=u.is_active,
                tenant_id=u.tenant_id,
            )
            for u in users
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@role_router.get(
    path="/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Get user by ID (admin)",
    description="Requires ADMIN or higher role. Tenant-scoped.",
    response_model=UserSchema,
    dependencies=[require_role(UserRole.ADMIN)],
)
async def get_user_by_id(
    user_id: UUID,
    current_user: GetCurrentUser,
    get_user_by_id_case: GetUserByIdCaseDep,
) -> UserSchema:
    """Get a single user by ID within the same tenant."""
    user = await get_user_by_id_case.execute(
        current_user=current_user,
        target_user_id=user_id,
    )
    return UserSchema(
        id=user.id,
        created_at=user.created_at,
        name=user.name,
        dni=user.dni,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        tenant_id=user.tenant_id,
    )


@role_router.delete(
    path="/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Deactivate a user (admin)",
    description="Requires ADMIN or higher role. Cannot deactivate self or last OWNER.",
    response_model=SimpleMessageSchema,
    dependencies=[require_role(UserRole.ADMIN)],
)
async def deactivate_user(
    user_id: UUID,
    current_user: GetCurrentUser,
    soft_delete_user_case: GetSoftDeleteUserCaseDep,
) -> SimpleMessageSchema:
    """Soft-delete a user by setting is_active=False."""
    await soft_delete_user_case.execute(
        current_user=current_user,
        target_user_id=user_id,
    )
    return SimpleMessageSchema(message="Usuario desactivado exitosamente")
