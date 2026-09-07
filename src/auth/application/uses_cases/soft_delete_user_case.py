"""Use case for soft-deleting (deactivating) a user."""

from uuid import UUID

from src.auth.domain.entities import UserEntity
from src.auth.domain.entities._user_role import UserRole
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.auth.domain.value_objects.user_value_object import UserUpdateValueObject
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotFoundError, NotPermissionError


class SoftDeleteUserCase:
    """Deactivates a user. Guards: not self, not last OWNER, same tenant, ADMIN+ role."""

    def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def execute(
        self,
        current_user: UserEntity,
        target_user_id: UUID,
    ) -> None:
        """Soft-delete a user by setting is_active=False.

        Args:
            current_user: The authenticated user performing the action.
            target_user_id: UUID of the user to deactivate.

        Raises:
            NotPermissionError: If trying to deactivate self.
            NotPermissionError: If missing permissions or cross-tenant.
            NotFoundError: If target user not found or tenant_id is None.
        """
        # Self-deactivation guard
        if current_user.id == target_user_id:
            raise NotPermissionError("No puedes desactivarte a ti mismo")

        # Role guard: must be ADMIN or higher
        if current_user.role.rank < UserRole.ADMIN.rank:
            raise NotPermissionError(
                "No tienes permisos suficientes para desactivar usuarios",
            )

        async with self.uow as uow:
            repo: IUserRepository = uow.get_repository(IUserRepository)

            target = await repo.get_by_id(target_user_id)
            if not target:
                raise NotFoundError("Usuario no encontrado")

            # Cross-tenant isolation
            if target.tenant_id != current_user.tenant_id:
                raise NotPermissionError(
                    "El usuario no pertenece a tu organización",
                )

            # Cannot deactivate the last OWNER
            if target.role == UserRole.OWNER:
                if current_user.tenant_id is None:
                    raise NotFoundError("Tenant no encontrado")
                # NOTE: Race condition — count_owners_by_tenant and the actual
                # deactivation are not atomic. In high-concurrency scenarios,
                # two concurrent requests could both see owner_count > 1 and
                # deactivate the last two owners simultaneously.
                # Future: use advisory lock or SERIALIZABLE isolation.
                owner_count = await repo.count_owners_by_tenant(
                    current_user.tenant_id,
                )
                if owner_count <= 1:
                    raise NotPermissionError(
                        "No puedes desactivar al único propietario del tenant",
                    )

            await repo.update_data(
                target_user_id,
                UserUpdateValueObject(is_active=False),
            )
            await uow.commit()
