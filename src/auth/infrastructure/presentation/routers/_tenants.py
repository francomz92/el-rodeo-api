"""Tenant router — tenant creation, invitations, and tenant lookup."""

from fastapi import APIRouter, Request, status

from src.auth.domain.entities._user_role import UserRole
from src.auth.infrastructure.adapters.http.input.authentication_schemas import (
    CreateTenantSchema,
)
from src.auth.infrastructure.adapters.http.input.role_schemas import InviteSchema
from src.auth.infrastructure.adapters.http.output.tenant_schemas import TenantResponseSchema
from src.auth.infrastructure.adapters.http.output.user_schemas import UserSchema
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCreateTenantCase,
    GetCurrentUser,
    require_role,
)
from src.auth.infrastructure.presentation.dependencies.role_dependencies import (
    GetInviteUserCase,
)
from src.auth.infrastructure.presentation.dependencies.tenant_dependencies import GetTenantCaseDep
from src.common.infrastructure.core import settings
from src.common.infrastructure.presentation.middlewares.rate_limiter import rate_limit

tenant_router = APIRouter(tags=["Authentication"])


@tenant_router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant with OWNER user",
    description="SUPER_ADMIN only. Creates a tenant with the given slug and creates the first user as OWNER.",
    response_model=UserSchema,
    dependencies=[require_role(UserRole.SUPER_ADMIN)],
)
@rate_limit("3/minute")
async def register_user(
    request: Request,
    data: CreateTenantSchema,
    create_tenant_case: GetCreateTenantCase,
):
    return await create_tenant_case.execute(
        tenant_name=data.tenant_name,
        slug=data.slug,
        name=data.name,
        dni=data.dni,
        email=data.email,
        redirect_url=f"{settings.DOMAIN}/confirm-account",
    )


@tenant_router.post(
    path="/invite",
    status_code=status.HTTP_201_CREATED,
    summary="Invite a user to the tenant",
    description="ADMIN or higher. Creates a user with role ≤ inviter's rank in the inviter's tenant.",
    response_model=UserSchema,
    dependencies=[require_role(UserRole.ADMIN)],
)
@rate_limit("5/minute")
async def invite_user(
    request: Request,
    data: InviteSchema,
    current_user: GetCurrentUser,
    invite_user_case: GetInviteUserCase,
):
    return await invite_user_case.execute(
        inviter=current_user,
        name=data.name,
        dni=data.dni,
        email=data.email,
        role=data.role,
        redirect_url=f"{settings.DOMAIN}/confirm-account",
    )


@tenant_router.get(
    path="/users/me/tenant",
    status_code=status.HTTP_200_OK,
    summary="Get current tenant info",
    response_model=TenantResponseSchema,
)
async def get_my_tenant(
    current_user: GetCurrentUser,
    get_tenant_case: GetTenantCaseDep,
):
    """Return the authenticated user's tenant info."""
    return await get_tenant_case.execute(current_user.tenant_id)
