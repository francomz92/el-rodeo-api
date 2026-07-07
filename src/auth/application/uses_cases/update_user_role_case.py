"""Use case for updating a user's role.

Orchestrates:
1. Loading the target user via the repository
2. Cross-tenant isolation check
3. Business rule validation via UpdateUserRoleService
4. Persisting the role change
5. Returning the updated user
"""

from uuid import UUID

from src.auth.domain.entities import UserEntity
from src.auth.domain.entities._user_role import UserRole
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.auth.domain.services.update_user_role_service import UpdateUserRoleService
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotPermissionError


class UpdateUserRoleCase:
    """Updates a user's role with full validation.

    Validates:
    - Actor has OWNER role
    - Actor is not changing their own role (self-escalation prevention)
    - Last OWNER protection (cannot demote the last OWNER in a tenant)
    - Cross-tenant isolation (actor and target must be in same tenant)
    """

    def __init__(
        self,
        uow: IUoW,
        update_user_role_service: UpdateUserRoleService,
    ) -> None:
        self.uow = uow
        self.service = update_user_role_service

    async def execute(
        self,
        actor: UserEntity,
        target_user_id: UUID,
        new_role: UserRole,
    ) -> UserEntity:
        """Execute the role update.

        Args:
            actor: The user performing the role change (must be OWNER).
            target_user_id: UUID of the user whose role is being changed.
            new_role: The role to assign to the target user.

        Returns:
            The updated UserEntity with the new role.

        Raises:
            ValueError: If the target user is not found.
            NotPermissionError: If any business rule prevents the change.
        """
        async with self.uow as uow:
            repo = uow.get_repository(IUserRepository)

            target = await repo.get_by_id(target_user_id)
            if not target:
                raise ValueError(
                    f"Usuario con ID '{target_user_id}' no encontrado",
                )

            # Cross-tenant isolation: actor and target must be in same tenant
            if target.tenant_id and actor.tenant_id and target.tenant_id != actor.tenant_id:
                raise NotPermissionError(
                    "No tienes permisos para modificar usuarios de otro tenant",
                )

            # Count owners for last-OWNER protection check
            assert actor.tenant_id is not None
            owners_count = await repo.count_owners_by_tenant(actor.tenant_id)

            # Validate business rules via domain service
            await self.service.can_update_role(
                actor=actor,
                target=target,
                new_role=new_role,
                owners_in_tenant=owners_count,
            )

            # Persist the role change
            await repo.update_role(target_user_id, new_role)
            await uow.commit()

            # Return the updated user
            updated = await repo.get_by_id(target_user_id)
            if updated is None:
                # Should never happen since we just validated the user exists
                msg = f"Usuario con ID '{target_user_id}' no encontrado después de actualizar"
                raise ValueError(msg)

            return updated
