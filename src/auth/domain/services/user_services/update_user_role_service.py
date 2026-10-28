"""Domain service for validating role update operations.

Pure business logic with no I/O dependencies. Validates:
- Only OWNER can change roles
- No self-escalation (user cannot change own role)
- Last OWNER protection (cannot demote the last OWNER)
"""

from src.auth.domain.entities._user_entity import UserEntity
from src.auth.domain.entities._user_role import UserRole
from src.common.domain.exceptions import NotPermissionError


class UpdateUserRoleService:
    """Validates role change business rules.

    All validation methods are async for consistency with the service
    pattern, but perform no I/O — they are pure domain logic.
    """

    async def can_update_role(
        self,
        actor: UserEntity,
        target: UserEntity,
        new_role: UserRole,
        owners_in_tenant: int,
    ) -> bool:
        """Validate that the role change is permitted by business rules.

        Args:
            actor: The user performing the role change.
            target: The user whose role is being changed.
            new_role: The target user's desired new role.
            owners_in_tenant: Current number of OWNERs in the actor's tenant.

        Returns:
            True if the role change is allowed.

        Raises:
            NotPermissionError: If any business rule prevents the change.
        """
        # Rule 1: Only OWNER can change roles
        if actor.role.rank < UserRole.OWNER.rank:
            raise NotPermissionError(
                "Solo los propietarios pueden cambiar roles",
            )

        # Rule 2: No self-escalation (user cannot change own role)
        if actor.id == target.id:
            raise NotPermissionError(
                "No puedes modificar tu propio rol",
            )

        # Rule 3: Last OWNER protection
        # When demoting an OWNER, verify at least one other OWNER remains
        if target.role == UserRole.OWNER and new_role != UserRole.OWNER:
            if owners_in_tenant <= 1:
                raise NotPermissionError(
                    "Debe haber al menos un propietario en el tenant",
                )

        # Rule 4: SUPER_ADMIN cannot be assigned via this service
        if new_role == UserRole.SUPER_ADMIN:
            raise NotPermissionError(
                "El rol SUPER_ADMIN no puede asignarse a través de este servicio",
            )

        # All rules passed, change is allowed
        return True
