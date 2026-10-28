"""Use case for retrieving a user by ID (admin only)."""

from uuid import UUID

from src.auth.domain.entities import UserEntity, UserRole
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotFoundError, NotPermissionError


class GetUserByIdCase:
    """Retrieves a user by ID, enforcing tenant isolation and admin role."""

    def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def execute(
        self,
        current_user: UserEntity,
        target_user_id: UUID,
    ) -> UserEntity:
        """Get a user by ID within the same tenant.

        Raises NotPermissionError if the current user lacks ADMIN role.
        Raises NotFoundError if the user is not found in the current tenant.
        """
        if current_user.role.rank < UserRole.ADMIN.rank:
            raise NotPermissionError("No tienes permisos suficientes para acceder a este recurso")

        async with self.uow as uow:
            repo: IUserRepository = uow.get_repository(IUserRepository)
            if current_user.tenant_id is None:
                raise NotFoundError("Tenant no encontrado")
            user = await repo.get_by_id_with_tenant_check(
                user_id=target_user_id,
                tenant_id=current_user.tenant_id,
            )
            if not user:
                raise NotFoundError("Usuario no encontrado")
            return user
